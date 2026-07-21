import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from app.domain.product.model import ProductMonitored
from app.domain.product.repository import ProductRepository
from app.domain.product.schemas import ProductCreate, ProductUpdate
from app.domain.price_history.model import PriceHistory
from app.domain.price_history.repository import PriceHistoryRepository
from app.domain.audit_log.model import AuditLog
from app.domain.audit_log.repository import AuditLogRepository


class ProductService:
    def __init__(
        self,
        product_repo: ProductRepository,
        audit_repo: AuditLogRepository,
        history_repo: PriceHistoryRepository
    ):
        self.product_repo = product_repo
        self.audit_repo = audit_repo
        self.history_repo = history_repo

    async def create_product(
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
        
        # Gera Log de Auditoria (SRP & Audit requirements)
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

    async def get_product_or_404(
        self, user_id: uuid.UUID, product_id: uuid.UUID
    ) -> ProductMonitored:
        product = await self.product_repo.get_by_user_and_id(user_id, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto monitorado não encontrado ou você não possui permissão para acessá-lo."
            )
        return product

    async def list_products(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[ProductMonitored]:
        return await self.product_repo.list_by_user(user_id, skip, limit)

    async def update_product(
        self,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        product_in: ProductUpdate,
        ip_address: Optional[str] = None
    ) -> ProductMonitored:
        product = await self.get_product_or_404(user_id, product_id)
        update_data = product_in.model_dump(exclude_unset=True)
        
        # Guardamos estado anterior para o log de auditoria
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
        
        # Gera Log de Auditoria
        audit = AuditLog(
            user_id=user_id,
            action="PRODUCT_UPDATE",
            details={
                "product_id": str(product.id),
                "changes": update_data,
                "previous_state": old_state
            },
            ip_address=ip_address
        )
        await self.audit_repo.create(audit)
        
        return updated_product

    async def delete_product(
        self, user_id: uuid.UUID, product_id: uuid.UUID, ip_address: Optional[str] = None
    ) -> None:
        product = await self.get_product_or_404(user_id, product_id)
        
        # Salva dados do produto antes de deletar
        product_details = {
            "product_id": str(product.id),
            "name": product.name,
            "url": product.url
        }
        
        await self.product_repo.delete(product)
        
        # Gera Log de Auditoria
        audit = AuditLog(
            user_id=user_id,
            action="PRODUCT_DELETE",
            details=product_details,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit)

    async def list_price_history(
        self, user_id: uuid.UUID, product_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[PriceHistory]:
        # Valida propriedade do produto antes de listar
        await self.get_product_or_404(user_id, product_id)
        return await self.history_repo.list_by_product(product_id, skip, limit)
