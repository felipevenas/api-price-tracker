from typing import Any
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    id: Any
    __name__: str

    # Gera __tablename__ automaticamente com base no nome da classe
    @declared_attr
    @classmethod
    def __tablename__(cls) -> str:
        # Ex: User -> user; ProductMonitored -> product_monitored
        import re
        name = cls.__name__
        parts = re.findall('[A-Z][a-z0-9]*', name)
        if not parts:
            return name.lower()
        return "_".join(part.lower() for part in parts)
