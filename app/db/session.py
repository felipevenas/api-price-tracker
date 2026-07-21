from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

from sqlalchemy.pool import NullPool

# Engine assíncrono para PostgreSQL
# Usamos NullPool para evitar conflitos de pool de conexões entre loops assíncronos do FastAPI e Celery
engine = create_async_engine(
    settings.ASYNC_DATABASE_URI,
    poolclass=NullPool,
    echo=False  # Mude para True para debugar queries geradas no console
)

# Fábrica de sessões assíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


# Dependência FastAPI para injetar a sessão nas requisições
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
