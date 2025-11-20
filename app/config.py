"""Application configuration using Pydantic Settings"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str = "sqlite:///./ai_x_manager.db"

    # X (Twitter) API
    twitter_api_key: str
    twitter_api_secret: str
    twitter_access_token: str
    twitter_access_token_secret: str
    twitter_bearer_token: Optional[str] = None

    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_deployment_name: str
    azure_openai_api_version: str = "2024-02-15-preview"

    # Application
    secret_key: str
    environment: str = "development"
    log_level: str = "INFO"

    # Scheduler
    scheduler_timezone: str = "UTC"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
