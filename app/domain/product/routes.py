import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.domain.user.model import User
from app.domain.product.repository import ProductRepository
from app.domain.product.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.domain.price_history.schemas import PriceHistoryResponse
from app.domain.audit_log.repository import AuditLogRepository
from app.domain.price_history.repository import PriceHistoryRepository
from app.domain.product.usecase import (
    CreateProductUseCase,
    ListProductsUseCase,
    GetProductUseCase,
    UpdateProductUseCase,
    DeleteProductUseCase,
    ListProductPriceHistoryUseCase,
)


def get_product_repository(db: AsyncSession = Depends(get_db)) -> ProductRepository:
    return ProductRepository(db)


def get_audit_log_repository(db: AsyncSession = Depends(get_db)) -> AuditLogRepository:
    return AuditLogRepository(db)


def get_price_history_repository(db: AsyncSession = Depends(get_db)) -> PriceHistoryRepository:
    return PriceHistoryRepository(db)


def get_create_product_use_case(
    product_repo: ProductRepository = Depends(get_product_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
) -> CreateProductUseCase:
    return CreateProductUseCase(product_repo, audit_repo)


def get_list_products_use_case(
    product_repo: ProductRepository = Depends(get_product_repository),
) -> ListProductsUseCase:
    return ListProductsUseCase(product_repo)


def get_product_use_case(
    product_repo: ProductRepository = Depends(get_product_repository),
) -> GetProductUseCase:
    return GetProductUseCase(product_repo)


def get_update_product_use_case(
    product_repo: ProductRepository = Depends(get_product_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
) -> UpdateProductUseCase:
    return UpdateProductUseCase(product_repo, audit_repo)


def get_delete_product_use_case(
    product_repo: ProductRepository = Depends(get_product_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
) -> DeleteProductUseCase:
    return DeleteProductUseCase(product_repo, audit_repo)


def get_list_price_history_use_case(
    product_repo: ProductRepository = Depends(get_product_repository),
    history_repo: PriceHistoryRepository = Depends(get_price_history_repository),
) -> ListProductPriceHistoryUseCase:
    return ListProductPriceHistoryUseCase(product_repo, history_repo)


router = APIRouter()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    use_case: CreateProductUseCase = Depends(get_create_product_use_case)
) -> Any:
    """
    Cadastra um novo produto para monitoramento de preços.
    Dispara imediatamente uma tarefa Celery assíncrona para coletar o preço inicial.
    """
    ip_address = request.client.host if request.client else None
    
    created_product = await use_case.execute(
        user_id=current_user.id,
        product_in=product_in,
        ip_address=ip_address
    )
    
    try:
        from app.infra.queue.tasks import check_product_price_task
        check_product_price_task.delay(str(created_product.id))
    except Exception:
        pass
        
    return created_product


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    use_case: ListProductsUseCase = Depends(get_list_products_use_case)
) -> Any:
    """
    Lista todos os produtos que o usuário logado está monitorando.
    """
    return await use_case.execute(user_id=current_user.id, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    use_case: GetProductUseCase = Depends(get_product_use_case)
) -> Any:
    """
    Recupera os detalhes de um produto monitorado específico.
    """
    return await use_case.execute(user_id=current_user.id, product_id=product_id)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    product_in: ProductUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    use_case: UpdateProductUseCase = Depends(get_update_product_use_case)
) -> Any:
    """
    Atualiza as configurações de monitoramento de um produto (ex: nome, preço alvo ou intervalo).
    """
    ip_address = request.client.host if request.client else None
    
    return await use_case.execute(
        user_id=current_user.id,
        product_id=product_id,
        product_in=product_in,
        ip_address=ip_address
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    use_case: DeleteProductUseCase = Depends(get_delete_product_use_case)
) -> None:
    """
    Remove um produto da lista de monitoramento.
    """
    ip_address = request.client.host if request.client else None
    
    await use_case.execute(
        user_id=current_user.id,
        product_id=product_id,
        ip_address=ip_address
    )


@router.get("/{product_id}/history", response_model=List[PriceHistoryResponse])
async def list_price_history(
    product_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    use_case: ListProductPriceHistoryUseCase = Depends(get_list_price_history_use_case)
) -> Any:
    """
    Retorna o histórico de variações de preço registradas para o produto especificado.
    """
    return await use_case.execute(
        user_id=current_user.id,
        product_id=product_id,
        skip=skip,
        limit=limit
    )
