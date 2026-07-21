import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.domain.user.model import User
from app.domain.product.repository import ProductRepository
from app.domain.product.service import ProductService
from app.domain.product.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.domain.price_history.repository import PriceHistoryRepository
from app.domain.price_history.schemas import PriceHistoryResponse
from app.domain.audit_log.repository import AuditLogRepository

router = APIRouter()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Cadastra um novo produto para monitoramento de preços.
    Dispara imediatamente uma tarefa Celery assíncrona para coletar o preço inicial.
    """
    product_repo = ProductRepository(db)
    audit_repo = AuditLogRepository(db)
    history_repo = PriceHistoryRepository(db)
    
    product_service = ProductService(product_repo, audit_repo, history_repo)
    
    # Obtém o IP do cliente para auditoria
    ip_address = request.client.host if request.client else None
    
    created_product = await product_service.create_product(
        user_id=current_user.id,
        product_in=product_in,
        ip_address=ip_address
    )
    
    # Dispara a tarefa Celery de raspagem de preço imediatamente em segundo plano (Fase 4)
    try:
        from app.infra.queue.tasks import check_product_price_task
        check_product_price_task.delay(str(created_product.id))
    except Exception:
        # Se o Celery/Redis não estiver inicializado ou rodando, a rota não quebra
        pass
        
    return created_product


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Lista todos os produtos que o usuário logado está monitorando.
    """
    product_repo = ProductRepository(db)
    audit_repo = AuditLogRepository(db)
    history_repo = PriceHistoryRepository(db)
    product_service = ProductService(product_repo, audit_repo, history_repo)
    
    return await product_service.list_products(user_id=current_user.id, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Recupera os detalhes de um produto monitorado específico.
    """
    product_repo = ProductRepository(db)
    audit_repo = AuditLogRepository(db)
    history_repo = PriceHistoryRepository(db)
    product_service = ProductService(product_repo, audit_repo, history_repo)
    
    return await product_service.get_product_or_404(user_id=current_user.id, product_id=product_id)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    product_in: ProductUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Atualiza as configurações de monitoramento de um produto (ex: nome, preço alvo ou intervalo).
    """
    product_repo = ProductRepository(db)
    audit_repo = AuditLogRepository(db)
    history_repo = PriceHistoryRepository(db)
    product_service = ProductService(product_repo, audit_repo, history_repo)
    
    ip_address = request.client.host if request.client else None
    
    return await product_service.update_product(
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
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Remove um produto da lista de monitoramento.
    """
    product_repo = ProductRepository(db)
    audit_repo = AuditLogRepository(db)
    history_repo = PriceHistoryRepository(db)
    product_service = ProductService(product_repo, audit_repo, history_repo)
    
    ip_address = request.client.host if request.client else None
    
    await product_service.delete_product(
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
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Retorna o histórico de variações de preço registradas para o produto especificado.
    """
    product_repo = ProductRepository(db)
    audit_repo = AuditLogRepository(db)
    history_repo = PriceHistoryRepository(db)
    product_service = ProductService(product_repo, audit_repo, history_repo)
    
    return await product_service.list_price_history(
        user_id=current_user.id,
        product_id=product_id,
        skip=skip,
        limit=limit
    )
