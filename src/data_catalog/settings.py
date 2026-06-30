"""Centralized application settings loaded from the .env file."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings resolved from environment variables or .env file.

    Attributes:
        gemini_api_key: Google AI Studio API key for Gemini models.
        h3_resolution: H3 hexagonal grid resolution for coordinate anonymization.
        mac_hash_salt: Secret salt used when hashing MAC addresses.
        postgres_host: PostgreSQL server hostname.
        postgres_port: PostgreSQL server port.
        postgres_db: Target database name.
        postgres_user: Database username.
        postgres_password: Database password.
        database_url: SQLAlchemy connection URL, built automatically from postgres fields.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str
    h3_resolution: int = 7
    mac_hash_salt: str = ""

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "data_catalog"
    postgres_user: str = "catalog_user"
    postgres_password: str

    database_url: str = ""

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        self.database_url = (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        return self


settings = Settings()
