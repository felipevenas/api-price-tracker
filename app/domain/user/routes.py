from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.domain.user.model import User
from app.domain.user.repository import UserRepository
from app.domain.user.service import UserService
from app.domain.user.schemas import UserResponse, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retorna os dados cadastrais do usuário atualmente autenticado.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Atualiza os dados cadastrais do usuário atualmente autenticado.
    """
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    user = await user_service.update_user(current_user.id, user_in)
    return user
