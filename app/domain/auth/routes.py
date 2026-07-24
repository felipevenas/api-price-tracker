from typing import Any
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domain.exceptions import ConflictError, NotFoundError
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserCreate
from app.domain.auth.usecase import RegisterUserUseCase, AuthenticateUserUseCase
from app.core.response import success_response, error_response

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Registra um novo usuário no sistema."""
    try:
        result = await RegisterUserUseCase(UserRepository(db)).execute(user_in)
        return success_response(data=result, message="Usuário registrado com sucesso")
    except ConflictError as e:
        return error_response(message="Erro ao registrar usuário", details=str(e))
    except Exception as e:
        return error_response(message="Erro inesperado ao registrar usuário", details=str(e))


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Autentica o usuário e retorna o token JWT."""
    try:
        result = await AuthenticateUserUseCase(UserRepository(db)).execute(form_data)
        return success_response(data=result, message="Login realizado com sucesso")
    except NotFoundError as e:
        return error_response(message="Credenciais inválidas", details=str(e))
    except Exception as e:
        return error_response(message="Erro inesperado ao realizar login", details=str(e))
