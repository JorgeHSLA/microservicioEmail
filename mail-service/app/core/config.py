from functools import lru_cache
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gmail_user: str
    gmail_password: SecretStr
    gmail_host: str = "smtp.gmail.com"
    gmail_port: int = 587
    from_name: str = "Turismo Platform"
    templates_dir: str = "app/templates"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
