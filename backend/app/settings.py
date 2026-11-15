from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration read from environment variables (prefix TECHDOC_) or a .env file."""

    model_config = SettingsConfigDict(env_prefix="TECHDOC_", env_file=".env", extra="ignore")

    api_key: SecretStr
    public_base_url: str = "http://localhost:8000"
    max_file_size_bytes: int = 10 * 1024 * 1024
