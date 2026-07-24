import uuid
from typing import Any
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.domain.exceptions import NotFoundError
from app.domain.user.model import User
from app.domain.product.repository import ProductRepository
from app.domain.price_history.repository import PriceHistoryRepository
from app.domain.audit_log.repository import AuditLogRepository
from app.domain.product.schemas import ProductCreate, ProductUpdate
from app.domain.product.usecase import (
    CreateProductUseCase,
    ListProductsUseCase,
    GetProductUseCase,
    UpdateProductUseCase,
    DeleteProductUseCase,
    ListProductPriceHistoryUseCase,
)
from app.core.response import success_response, error_response

router = APIRouter()


def _build_use_cases(db: AsyncSession):
    """Monta todos os repositórios e retorna um dicionário de use cases prontos para uso."""
    product_repo = ProductRepository(db)
    audit_repo = AuditLogRepository(db)
    history_repo = PriceHistoryRepository(db)
    return {
        "create": CreateProductUseCase(product_repo, audit_repo),
        "list": ListProductsUseCase(product_repo),
        "get": GetProductUseCase(product_repo),
        "update": UpdateProductUseCase(product_repo, audit_repo),
        "delete": DeleteProductUseCase(product_repo, audit_repo),
        "history": ListProductPriceHistoryUseCase(product_repo, history_repo),
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Cadastra um produto para monitoramento e dispara a checagem inicial."""
    try:
        ip = request.client.host if request.client else None
        uc = _build_use_cases(db)
        created = await uc["create"].execute(current_user.id, product_in, ip)

        try:
            from app.infra.worker.tasks.price_check import check_product_price_task
            check_product_price_task.delay(str(created.id))
        except Exception:
            pass

        return success_response(data=created, message="Produto cadastrado com sucesso")
    except Exception as e:
        return error_response(message="Erro ao cadastrar produto", details=str(e))


@router.get("/")
async def list_products(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Lista todos os produtos monitorados pelo usuário autenticado."""
    try:
        uc = _build_use_cases(db)
        products = await uc["list"].execute(current_user.id, skip, limit)
        return success_response(data=products, message="Produtos listados com sucesso")
    except Exception as e:
        return error_response(message="Erro ao listar produtos", details=str(e))


@router.get("/{product_id}")
async def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retorna os detalhes de um produto monitorado."""
    try:
        uc = _build_use_cases(db)
        product = await uc["get"].execute(current_user.id, product_id)
        return success_response(data=product, message="Produto recuperado com sucesso")
    except NotFoundError as e:
        return error_response(message="Produto não encontrado", details=str(e))
    except Exception as e:
        return error_response(message="Erro ao obter detalhes do produto", details=str(e))


@router.put("/{product_id}")
async def update_product(
    product_id: uuid.UUID,
    product_in: ProductUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Atualiza as configurações de monitoramento de um produto."""
    try:
        ip = request.client.host if request.client else None
        uc = _build_use_cases(db)
        updated = await uc["update"].execute(current_user.id, product_id, product_in, ip)
        return success_response(data=updated, message="Produto atualizado com sucesso")
    except NotFoundError as e:
        return error_response(message="Produto não encontrado", details=str(e))
    except Exception as e:
        return error_response(message="Erro ao atualizar produto", details=str(e))


@router.delete("/{product_id}")
async def delete_product(
    product_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Remove um produto da lista de monitoramento."""
    try:
        ip = request.client.host if request.client else None
        uc = _build_use_cases(db)
        await uc["delete"].execute(current_user.id, product_id, ip)
        return success_response(message="Produto removido com sucesso")
    except NotFoundError as e:
        return error_response(message="Produto não encontrado", details=str(e))
    except Exception as e:
        return error_response(message="Erro ao remover produto", details=str(e))


@router.get("/{product_id}/history")
async def list_price_history(
    product_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retorna o histórico de variações de preço de um produto."""
    try:
        uc = _build_use_cases(db)
        history = await uc["history"].execute(current_user.id, product_id, skip, limit)
        return success_response(data=history, message="Histórico de preços listado com sucesso")
    except NotFoundError as e:
        return error_response(message="Produto não encontrado", details=str(e))
    except Exception as e:
        return error_response(message="Erro ao listar histórico de preços", details=str(e))
