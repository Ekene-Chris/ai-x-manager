"""Application configuration using Pydantic Settings"""

from pydantic_settings import BaseSettings
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str = "sqlite:///./ai_x_manager.db"

    # X (Twitter) API - OAuth 2.0 (Recommended)
    twitter_client_id: Optional[str] = None
    twitter_client_secret: Optional[str] = None
    twitter_redirect_uri: str = "http://localhost:8000/api/auth/twitter/callback"

    # X (Twitter) API - Legacy (Optional - for direct API keys)
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_token_secret: Optional[str] = None
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

    # Dashboard Authentication (Optional but recommended for production)
    dashboard_username: Optional[str] = None
    dashboard_password: Optional[str] = None

    # Scheduler
    scheduler_timezone: str = "UTC"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Debug logging for configuration
logger.info(f"Environment: {settings.environment}")
logger.info(f"Twitter Client ID set: {bool(settings.twitter_client_id)}")
logger.info(f"Twitter Client Secret set: {bool(settings.twitter_client_secret)}")
logger.info(f"Twitter Redirect URI: {settings.twitter_redirect_uri}")

# Check raw environment variables
if settings.environment == "production":
    logger.info("Checking raw environment variables:")
    logger.info(f"  TWITTER_CLIENT_ID env var: {bool(os.getenv('TWITTER_CLIENT_ID'))}")
    logger.info(f"  twitter_client_id env var: {bool(os.getenv('twitter_client_id'))}")

    # Log first few characters if set
    client_id = os.getenv('TWITTER_CLIENT_ID') or os.getenv('twitter_client_id')
    if client_id:
        logger.info(f"  Client ID starts with: {client_id[:10]}...")
    else:
        logger.warning("  No Twitter Client ID found in environment variables!")
