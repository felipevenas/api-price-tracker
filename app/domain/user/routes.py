from typing import Any
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_user_repository
from app.domain.user.model import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserResponse, UserUpdate
from app.domain.user.usecase import UpdateUserUseCase


def get_update_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UpdateUserUseCase:
    return UpdateUserUseCase(user_repo)


router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_user_authenticated(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retorna os dados cadastrais do usuário atualmente autenticado.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_authenticated(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case)
) -> Any:
    """
    Atualiza os dados cadastrais do usuário atualmente autenticado.
    """
    return await use_case.execute(current_user.id, user_in)
