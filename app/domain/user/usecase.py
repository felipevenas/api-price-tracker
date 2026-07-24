import uuid
from typing import Optional

from app.core.security import get_password_hash
from app.domain.user.model import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserUpdate
from app.domain.exceptions import ConflictError, NotFoundError


class UpdateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: uuid.UUID, user_in: UserUpdate) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado.")

        update_data = user_in.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            user.password_hash = get_password_hash(update_data["password"])

        if "email" in update_data and update_data["email"]:
            if update_data["email"] != user.email:
                if await self.user_repo.get_by_email(update_data["email"]):
                    raise ConflictError("Este email já está em uso por outro usuário.")
            user.email = update_data["email"]

        if "full_name" in update_data:
            user.full_name = update_data["full_name"]

        if "is_active" in update_data:
            user.is_active = update_data["is_active"]

        return await self.user_repo.save(user)
