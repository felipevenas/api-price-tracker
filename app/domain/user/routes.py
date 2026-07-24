from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.domain.exceptions import ConflictError, NotFoundError
from app.domain.user.model import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserUpdate, UserResponse
from app.domain.user.usecase import UpdateUserUseCase
from app.core.response import success_response, error_response

router = APIRouter()


@router.get(
    "/me",
    summary="Obter perfil do usuário autenticado",
)
async def get_user_authenticated(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retorna os dados cadastrais do usuário autenticado."""
    try:
        return success_response(data=UserResponse.model_validate(current_user), message="Perfil do usuário recuperado com sucesso")
    except Exception as e:
        return error_response(message="Erro ao recuperar dados do usuário", details=str(e))


@router.put(
    "/me",
    summary="Atualizar perfil do usuário autenticado",
)
async def update_user_authenticated(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Atualiza os dados cadastrais do usuário autenticado."""
    try:
        result = await UpdateUserUseCase(UserRepository(db)).execute(current_user.id, user_in)
        return success_response(data=UserResponse.model_validate(result), message="Perfil do usuário atualizado com sucesso")
    except (NotFoundError, ConflictError) as e:
        return error_response(message="Erro ao atualizar dados do usuário", details=str(e))
    except Exception as e:
        return error_response(message="Erro inesperado ao atualizar perfil", details=str(e))
