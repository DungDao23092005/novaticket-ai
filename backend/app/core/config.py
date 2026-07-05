"""
core/config.py — Centralized application configuration.

All configuration values come from environment variables or .env file.
Never hardcode secrets, URLs, or environment-specific values elsewhere.

Usage:
    from app.core.config import settings
    print(settings.app_name)
"""

from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    pydantic-settings automatically reads from .env file and env vars.
    Environment variables take precedence over .env file values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars not defined here
        protected_namespaces=("settings_",),  # Fix: suppress false positive warning for model_dir field
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_name: str = "NovaTicket API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ------------------------------------------------------------------
    # Microsoft SQL Server
    # ------------------------------------------------------------------
    mssql_server: str = "localhost"
    mssql_port: int = 1433
    mssql_database: str = "novaticket"
    mssql_user: str = "sa"
    mssql_password: str
    mssql_driver: str = "ODBC Driver 18 for SQL Server"

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # ------------------------------------------------------------------
    # ML Model Artifacts
    # ------------------------------------------------------------------
    model_dir: str = "models"

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------
    @property
    def database_url(self) -> str:
        """
        Build SQLAlchemy connection string for SQL Server via pyodbc.
        TrustServerCertificate=yes is required for local dev with self-signed cert.

        IMPORTANT: Password is URL-encoded with quote_plus() to handle special
        characters like @, #, !, ? which would otherwise break URL parsing.
        Example: 'NovaTicket@2024!' → 'NovaTicket%402024%21'
        """
        driver_encoded = self.mssql_driver.replace(" ", "+")
        password_encoded = quote_plus(self.mssql_password)  # Encode @, #, !, etc.
        return (
            f"mssql+pyodbc://{self.mssql_user}:{password_encoded}"
            f"@{self.mssql_server}:{self.mssql_port}/{self.mssql_database}"
            f"?driver={driver_encoded}"
            f"&TrustServerCertificate=yes"
        )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS string into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    lru_cache ensures Settings is only instantiated once per process.
    This is the recommended pattern for FastAPI dependency injection.
    """
    return Settings()


# Module-level singleton for direct imports (convenience)
settings = get_settings()
