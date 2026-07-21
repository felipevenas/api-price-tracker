import uuid
from typing import Optional
from fastapi import HTTPException, status
from app.domain.user.model import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return await self.repository.get_by_id(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.repository.get_by_email(email)

    async def create_user(self, user_in: UserCreate) -> User:
        # Verifica se o email já existe
        existing_user = await self.repository.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este endereço de email já está cadastrado no sistema."
            )
        
        # Cria a entidade
        hashed_password = get_password_hash(user_in.password)
        new_user = User(
            email=user_in.email,
            password_hash=hashed_password,
            full_name=user_in.full_name,
            is_active=True
        )
        return await self.repository.create(new_user)

    async def update_user(self, user_id: uuid.UUID, user_in: UserUpdate) -> User:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
            
        update_data = user_in.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            user.password_hash = get_password_hash(update_data["password"])
            
        if "email" in update_data and update_data["email"]:
            # Verifica duplicidade de email
            if update_data["email"] != user.email:
                existing = await self.repository.get_by_email(update_data["email"])
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Este email já está em uso por outro usuário."
                    )
            user.email = update_data["email"]
            
        if "full_name" in update_data:
            user.full_name = update_data["full_name"]
            
        if "is_active" in update_data:
            user.is_active = update_data["is_active"]
            
        return await self.repository.save(user)
