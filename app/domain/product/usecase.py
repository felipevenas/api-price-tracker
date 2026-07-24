import uuid
from datetime import datetime
from typing import List, Optional

from app.domain.product.model import ProductMonitored
from app.domain.product.repository import ProductRepository
from app.domain.product.schemas import ProductCreate, ProductUpdate
from app.domain.audit_log.model import AuditLog
from app.domain.audit_log.repository import AuditLogRepository
from app.domain.price_history.model import PriceHistory
from app.domain.price_history.repository import PriceHistoryRepository
from app.domain.exceptions import NotFoundError
from app.domain.mercado_livre.usecase import GetMercadoLivrePriceByUrlUseCase
from app.helpers.url_parser import get_domain_name
from app.infra.scrapers.selenium_scraper import ScraperFactory
from app.infra.logging.logger import logger

_MERCADO_LIVRE_DOMAINS = {"mercadolivre.com.br", "mercadolivre.com", "produto.mercadolivre.com.br"}


def _is_mercado_livre(url: str) -> bool:
    domain = get_domain_name(url)
    return any(ml in domain for ml in _MERCADO_LIVRE_DOMAINS)


def _get_price(url: str) -> Optional[float]:
    """
    Roteia a consulta de preço para o provider correto:
    - Mercado Livre → API Oficial (GetMercadoLivrePriceByUrlUseCase)
    - Outros domínios → ScraperFactory (Selenium)
    """
    if _is_mercado_livre(url):
        result = GetMercadoLivrePriceByUrlUseCase().execute(url)
        return result.price
    scraper = ScraperFactory.get_scraper(url)
    return scraper.scrape(url)


class CreateProductUseCase:
    def __init__(self, product_repo: ProductRepository, audit_repo: AuditLogRepository):
        self.product_repo = product_repo
        self.audit_repo = audit_repo

    async def execute(
        self, user_id: uuid.UUID, product_in: ProductCreate, ip_address: Optional[str] = None
    ) -> ProductMonitored:
        product = ProductMonitored(
            user_id=user_id,
            name=product_in.name,
            url=product_in.url,
            target_price=product_in.target_price,
            check_interval_minutes=product_in.check_interval_minutes,
            active=True,
        )
        created = await self.product_repo.create(product)

        await self.audit_repo.create(AuditLog(
            user_id=user_id,
            action="PRODUCT_CREATE",
            details={
                "product_id": str(created.id),
                "name": created.name,
                "url": created.url,
                "target_price": created.target_price,
                "check_interval_minutes": created.check_interval_minutes,
            },
            ip_address=ip_address,
        ))
        return created


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

    async def execute(self, user_id: uuid.UUID, product_id: uuid.UUID) -> ProductMonitored:
        product = await self.product_repo.get_by_user_and_id(user_id, product_id)
        if not product:
            raise NotFoundError(
                "Produto monitorado não encontrado ou você não possui permissão para acessá-lo."
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
        ip_address: Optional[str] = None,
    ) -> ProductMonitored:
        product = await self.product_repo.get_by_user_and_id(user_id, product_id)
        if not product:
            raise NotFoundError(
                "Produto monitorado não encontrado ou você não possui permissão para acessá-lo."
            )

        update_data = product_in.model_dump(exclude_unset=True)
        old_state = {
            "name": product.name,
            "target_price": product.target_price,
            "check_interval_minutes": product.check_interval_minutes,
            "active": product.active,
        }

        for field in ("name", "target_price", "check_interval_minutes", "active"):
            if field in update_data:
                setattr(product, field, update_data[field])

        updated = await self.product_repo.save(product)

        await self.audit_repo.create(AuditLog(
            user_id=user_id,
            action="PRODUCT_UPDATE",
            details={
                "product_id": str(updated.id),
                "changes": update_data,
                "previous_state": old_state,
            },
            ip_address=ip_address,
        ))
        return updated


class DeleteProductUseCase:
    def __init__(self, product_repo: ProductRepository, audit_repo: AuditLogRepository):
        self.product_repo = product_repo
        self.audit_repo = audit_repo

    async def execute(
        self, user_id: uuid.UUID, product_id: uuid.UUID, ip_address: Optional[str] = None
    ) -> None:
        product = await self.product_repo.get_by_user_and_id(user_id, product_id)
        if not product:
            raise NotFoundError(
                "Produto monitorado não encontrado ou você não possui permissão para acessá-lo."
            )

        product_details = {"product_id": str(product.id), "name": product.name, "url": product.url}
        await self.product_repo.delete(product)

        await self.audit_repo.create(AuditLog(
            user_id=user_id,
            action="PRODUCT_DELETE",
            details=product_details,
            ip_address=ip_address,
        ))


class ListProductPriceHistoryUseCase:
    def __init__(self, product_repo: ProductRepository, history_repo: PriceHistoryRepository):
        self.product_repo = product_repo
        self.history_repo = history_repo

    async def execute(
        self, user_id: uuid.UUID, product_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[PriceHistory]:
        product = await self.product_repo.get_by_user_and_id(user_id, product_id)
        if not product:
            raise NotFoundError(
                "Produto monitorado não encontrado ou você não possui permissão para acessá-lo."
            )
        return await self.history_repo.get_by_product(product_id, skip, limit)


class CheckProductPriceUseCase:
    """
    Executa a checagem de preço de um produto monitorado.
    Atualiza o preço corrente, registra histórico e auditoria.
    Sempre atualiza last_checked_at (inclusive em falha) para respeitar o check_interval_minutes.
    """

    def __init__(
        self,
        product_repo: ProductRepository,
        audit_repo: AuditLogRepository,
        history_repo: PriceHistoryRepository,
    ):
        self.product_repo = product_repo
        self.audit_repo = audit_repo
        self.history_repo = history_repo

    async def execute(self, product_id: uuid.UUID) -> str:
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            logger.error(f"Produto ID {product_id} não encontrado. Tarefa abortada.")
            return "abort_not_found"

        if not product.active:
            logger.warning(f"Produto ID {product_id} está inativo. Tarefa abortada.")
            return "abort_inactive"

        logger.info(f"Checando preço para: {product.url}")

        try:
            price = _get_price(product.url)

            if price is None or price <= 0:
                raise ValueError("Preço retornado nulo ou zero.")

            logger.info(f"Preço obtido: R$ {price:.2f}")
            old_price = product.current_price
            product.current_price = price
            product.last_checked_at = datetime.utcnow()
            await self.product_repo.save(product)

            await self.history_repo.create(PriceHistory(
                product_id=product.id,
                price=price,
                status="success",
            ))
            await self.audit_repo.create(AuditLog(
                user_id=product.user_id,
                action="PRICE_CHECK_SUCCESS",
                details={
                    "product_id": str(product.id),
                    "name": product.name,
                    "old_price": float(old_price) if old_price is not None else None,
                    "new_price": float(price),
                    "price_dropped": (price < old_price) if old_price is not None else False,
                },
            ))
            return f"success_price_{price:.2f}"

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Falha ao checar preço do produto {product_id}: {error_msg}")

            # Atualiza last_checked_at para respeitar o intervalo individual do produto
            product.last_checked_at = datetime.utcnow()
            await self.product_repo.save(product)

            await self.history_repo.create(PriceHistory(
                product_id=product.id,
                price=None,
                status="failed",
                error_message=error_msg[:450],
            ))
            await self.audit_repo.create(AuditLog(
                user_id=product.user_id,
                action="PRICE_CHECK_FAILED",
                details={"product_id": str(product.id), "url": product.url, "error": error_msg},
            ))
            return f"failed_{error_msg[:100]}"
