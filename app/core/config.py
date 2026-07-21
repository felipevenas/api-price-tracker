import os
from typing import Any, Dict, Optional
from pydantic import Field, PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Price Monitor API"
    API_V1_STR: str = "/api/v1"
    
    # Segurança e Autenticação
    SECRET_KEY: str = Field(default="SUPER_SECRET_KEY_CHANGE_ME_IN_PRODUCTION")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias padrão
    
    # Banco de Dados PostgreSQL
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "price_monitor"
    POSTGRES_PORT: str = "5432"
    ASYNC_DATABASE_URI: Optional[str] = None

    @field_validator("ASYNC_DATABASE_URI", mode="before")
    @classmethod
    def assemble_async_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str) and v:
            return v
        data = info.data
        return f"postgresql+asyncpg://{data.get('POSTGRES_USER')}:{data.get('POSTGRES_PASSWORD')}@{data.get('POSTGRES_SERVER')}:{data.get('POSTGRES_PORT')}/{data.get('POSTGRES_DB')}"

    # Enfileirador e Fila
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Scraping (Selenium Grid / Standalone Chrome)
    SELENIUM_HUB_URL: Optional[str] = None  # Se setado, usa WebDriver remoto. Se nulo, roda local headless
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
