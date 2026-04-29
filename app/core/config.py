import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Domain Email Intelligence Engine"
    
    # Use .env file if available
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://postgres:password@localhost:5432/email_engine"
    )

    PROXY_URL: str | None = os.getenv("PROXY_URL", None)

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

settings = Settings()

