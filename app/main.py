"""Main FastAPI application"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import logging

from app.config import settings
from app.database import init_db
from app.api import tweets, ai, analytics, auth
from app.services.scheduler_service import SchedulerService
from app.services.twitter_service import TwitterService
from app.services.twitter_oauth_service import TwitterOAuthService
from app.services.llm_service import LLMService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global service instances
scheduler_service = None
twitter_service = None
llm_service = None
oauth_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting AI X Account Manager...")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Initialize services
    global scheduler_service, twitter_service, llm_service, oauth_service

    # Initialize OAuth service if configured
    if settings.twitter_client_id and settings.twitter_client_secret:
        try:
            oauth_service = TwitterOAuthService()
            auth.set_oauth_service(oauth_service)
            logger.info("Twitter OAuth service initialized")
        except Exception as e:
            logger.warning(f"Twitter OAuth not configured: {e}")

    # Initialize Twitter service (legacy mode or fallback)
    try:
        twitter_service = TwitterService()
        logger.info("Twitter service initialized")
    except Exception as e:
        logger.warning(f"Twitter service not available: {e}")
        logger.info("Use OAuth authentication via /api/auth/twitter/login")

    try:
        llm_service = LLMService()
        logger.info("LLM service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize LLM service: {e}")

    try:
        scheduler_service = SchedulerService()
        scheduler_service.start()
        logger.info("Scheduler service started")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler service: {e}")

    # Set service instances in API routers
    tweets.set_services(scheduler_service, twitter_service)
    ai.set_llm_service(llm_service)

    logger.info("All services initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down AI X Account Manager...")
    if scheduler_service:
        scheduler_service.shutdown()
        logger.info("Scheduler service stopped")


# Create FastAPI app
app = FastAPI(
    title="AI X Account Manager",
    description="AI-powered Twitter/X account management system",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(tweets.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "twitter": twitter_service is not None,
            "llm": llm_service is not None,
            "scheduler": scheduler_service is not None and scheduler_service.scheduler.running,
        },
    }


# Root endpoint - serve web UI
@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serve the interactive web dashboard"""
    dashboard_path = Path(__file__).parent / "static" / "dashboard.html"
    with open(dashboard_path, "r") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False,
    )
