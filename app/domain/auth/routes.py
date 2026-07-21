from typing import Any
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_user_repository
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserCreate, UserResponse
from app.domain.auth.usecase import RegisterUserUseCase, AuthenticateUserUseCase


def get_register_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository)
) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_repo)


def get_authenticate_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthenticateUserUseCase:
    return AuthenticateUserUseCase(user_repo)


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    use_case: RegisterUserUseCase = Depends(get_register_user_use_case)
) -> Any:
    """
    Registra um novo usuário no sistema.
    """
    return await use_case.execute(user_in)


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    use_case: AuthenticateUserUseCase = Depends(get_authenticate_user_use_case)
) -> Any:
    """
    Autentica o usuário e retorna o token JWT (compatível com Swagger OAuth2).
    """
    return await use_case.execute(form_data)
