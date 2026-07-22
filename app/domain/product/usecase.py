import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status

from app.domain.product.model import ProductMonitored
from app.domain.product.repository import ProductRepository
from app.domain.product.schemas import ProductCreate, ProductUpdate
from app.domain.audit_log.model import AuditLog
from app.domain.audit_log.repository import AuditLogRepository
from app.domain.price_history.model import PriceHistory
from app.domain.price_history.repository import PriceHistoryRepository
from app.infra.scrapers.factory import ScraperFactory
from app.infra.logging.logger import logger


class CreateProductUseCase:
    def __init__(self, product_repo: ProductRepository, audit_repo: AuditLogRepository):
        self.product_repo = product_repo
        self.audit_repo = audit_repo

    async def execute(
        self, user_id: uuid.UUID, product_in: ProductCreate, ip_address: Optional[str] = None
    ) -> ProductMonitored:
        new_product = ProductMonitored(
            user_id=user_id,
            name=product_in.name,
            url=product_in.url,
            target_price=product_in.target_price,
            check_interval_minutes=product_in.check_interval_minutes,
            active=True
        )
        created_product = await self.product_repo.create(new_product)
        
        audit = AuditLog(
            user_id=user_id,
            action="PRODUCT_CREATE",
            details={
                "product_id": str(created_product.id),
                "name": created_product.name,
                "url": created_product.url,
                "target_price": created_product.target_price,
                "check_interval_minutes": created_product.check_interval_minutes
            },
            ip_address=ip_address
        )
        await self.audit_repo.create(audit)
        return created_product


class ListProductsUseCase:
    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    async def execute(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[ProductMonitored]:
        return await self.product_repo.get_by_user(user_id, skip, limit)


class GetProductUseCase:
    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    async def execute(
        self, user_id: uuid.UUID, product_id: uuid.UUID
    ) -> ProductMonitored:
        product = await self.product_repo.get_by_user_and_id(user_id, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto monitorado não encontrado ou você não possui permissão para acessá-lo."
            )
        return product


class UpdateProductUseCase:
    def __init__(self, product_repo: ProductRepository, audit_repo: AuditLogRepository):
        self.product_repo = product_repo
        self.audit_repo = audit_repo

    async def execute(
        self,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        product_in: ProductUpdate,
        ip_address: Optional[str] = None
    ) -> ProductMonitored:
        product = await self.product_repo.get_by_user_and_id(user_id, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto monitorado não encontrado ou você não possui permissão para acessá-lo."
            )
            
        update_data = product_in.model_dump(exclude_unset=True)
        old_state = {
            "name": product.name,
            "target_price": product.target_price,
            "check_interval_minutes": product.check_interval_minutes,
            "active": product.active
        }
        
        if "name" in update_data:
            product.name = update_data["name"]
        if "target_price" in update_data:
            product.target_price = update_data["target_price"]
        if "check_interval_minutes" in update_data:
            product.check_interval_minutes = update_data["check_interval_minutes"]
        if "active" in update_data:
            product.active = update_data["active"]
            
        updated_product = await self.product_repo.save(product)
        
        audit = AuditLog(
            user_id=user_id,
            action="PRODUCT_UPDATE",
            details={
                "product_id": str(updated_product.id),
                "changes": update_data,
                "previous_state": old_state
            },
            ip_address=ip_address
        )
        await self.audit_repo.create(audit)
        return updated_product


class DeleteProductUseCase:
    def __init__(self, product_repo: ProductRepository, audit_repo: AuditLogRepository):
        self.product_repo = product_repo
        self.audit_repo = audit_repo

    async def execute(
        self, user_id: uuid.UUID, product_id: uuid.UUID, ip_address: Optional[str] = None
    ) -> None:
        product = await self.product_repo.get_by_user_and_id(user_id, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto monitorado não encontrado ou você não possui permissão para acessá-lo."
            )
            
        product_details = {
            "product_id": str(product.id),
            "name": product.name,
            "url": product.url
        }
        
        await self.product_repo.delete(product)
        
        audit = AuditLog(
            user_id=user_id,
            action="PRODUCT_DELETE",
            details=product_details,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit)


class ListProductPriceHistoryUseCase:
    def __init__(self, product_repo: ProductRepository, history_repo: PriceHistoryRepository):
        self.product_repo = product_repo
        self.history_repo = history_repo

    async def execute(
        self, user_id: uuid.UUID, product_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[PriceHistory]:
        product = await self.product_repo.get_by_user_and_id(user_id, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto monitorado não encontrado ou você não possui permissão para acessá-lo."
            )
        return await self.history_repo.get_by_product(product_id, skip, limit)


class CheckProductPriceUseCase:
    def __init__(
        self,
        product_repo: ProductRepository,
        audit_repo: AuditLogRepository,
        history_repo: PriceHistoryRepository
    ):
        self.product_repo = product_repo
        self.audit_repo = audit_repo
        self.history_repo = history_repo

    async def execute(self, product_uuid: uuid.UUID) -> str:
        product = await self.product_repo.get_by_id(product_uuid)
        if not product:
            logger.error(f"Tarefa abortada. Produto ID {product_uuid} não encontrado no banco.")
            return "abort_not_found"
            
        if not product.active:
            logger.warning(f"Tarefa abortada. Produto ID {product_uuid} está inativo no momento.")
            return "abort_inactive"

        logger.info(f"Processando URL: {product.url}")
        
        try:
            scraper = ScraperFactory.get_scraper(product.url)
            logger.info("Scraper instanciado com sucesso. Iniciando execução do Selenium...")
            price = scraper.scrape(product.url)
            
            if price is not None and price > 0:
                logger.info(f"Preço extraído com sucesso: R$ {price:.2f}")
                
                old_price = product.current_price
                product.current_price = price
                product.last_checked_at = datetime.utcnow()
                await self.product_repo.save(product)
                
                history = PriceHistory(
                    product_id=product.id,
                    price=price,
                    status="success"
                )
                await self.history_repo.create(history)
                
                audit = AuditLog(
                    user_id=product.user_id,
                    action="PRICE_CHECK_SUCCESS",
                    details={
                        "product_id": str(product.id),
                        "name": product.name,
                        "old_price": float(old_price) if old_price is not None else None,
                        "new_price": float(price),
                        "price_dropped": (price < old_price) if old_price is not None else False
                    }
                )
                await self.audit_repo.create(audit)
                return f"success_price_{price:.2f}"
            else:
                raise ValueError("Scraper retornou preço nulo ou zero.")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Falha ao checar preço do produto {product_uuid}: {error_msg}")
            
            history = PriceHistory(
                product_id=product.id,
                price=None,
                status="failed",
                error_message=error_msg[:450]
            )
            await self.history_repo.create(history)
            
            audit = AuditLog(
                user_id=product.user_id,
                action="PRICE_CHECK_FAILED",
                details={
                    "product_id": str(product.id),
                    "url": product.url,
                    "error": error_msg
                }
            )
            await self.audit_repo.create(audit)
            return f"failed_{error_msg[:100]}"
