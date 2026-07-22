from datetime import timedelta
from typing import Dict
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.domain.user.model import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserCreate


class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_in: UserCreate) -> User:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este endereço de email já está cadastrado no sistema."
            )
            
        hashed_password = get_password_hash(user_in.password)
        new_user = User(
            email=user_in.email,
            password_hash=hashed_password,
            full_name=user_in.full_name,
            is_active=True
        )
        return await self.user_repo.create(new_user)


class AuthenticateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, form_data: OAuth2PasswordRequestForm) -> Dict[str, str]:
        user = await self.user_repo.get_by_email(form_data.username)
        
        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail ou senha incorretos."
            )
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário inativo no sistema."
            )
            
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
