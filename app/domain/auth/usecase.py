from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.domain.user.model import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserCreate
from app.domain.exceptions import ConflictError, NotFoundError
from datetime import timedelta
from typing import Dict


class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_in: UserCreate) -> User:
        if await self.user_repo.get_by_email(user_in.email):
            raise ConflictError("Este endereço de email já está cadastrado no sistema.")

        hashed_password = get_password_hash(user_in.password)
        return await self.user_repo.create(User(
            email=user_in.email,
            password_hash=hashed_password,
            full_name=user_in.full_name,
            is_active=True,
        ))


class AuthenticateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, form_data: OAuth2PasswordRequestForm) -> Dict[str, str]:
        user = await self.user_repo.get_by_email(form_data.username)

        if not user or not verify_password(form_data.password, user.password_hash):
            raise NotFoundError("E-mail ou senha incorretos.")

        if not user.is_active:
            raise NotFoundError("Usuário inativo no sistema.")

        expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(subject=user.id, expires_delta=expires)
        return {"access_token": token, "token_type": "bearer"}
