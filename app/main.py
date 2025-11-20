"""Main FastAPI application"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
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
    """Serve the web UI"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI X Account Manager</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }

        h1 {
            color: #1DA1F2;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #666;
            font-size: 1.1em;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
        }

        .card h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3em;
        }

        .card p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }

        .button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }

        .button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }

        .button-secondary {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        .api-docs {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }

        .api-docs h2 {
            color: #333;
            margin-bottom: 20px;
        }

        .endpoint {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #1DA1F2;
        }

        .endpoint code {
            color: #667eea;
            font-weight: 600;
        }

        .method {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 10px;
        }

        .get { background: #61affe; color: white; }
        .post { background: #49cc90; color: white; }
        .put { background: #fca130; color: white; }
        .delete { background: #f93e3e; color: white; }

        .footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI X Account Manager</h1>
            <p class="subtitle">Intelligent Twitter/X account management powered by Azure OpenAI</p>
        </div>

        <div class="grid">
            <div class="card">
                <h2>🐦 Connect Twitter</h2>
                <p>Authenticate with Twitter using OAuth 2.0. Simple "Sign in with Twitter" - no API keys needed!</p>
                <a href="/api/auth/twitter/login" class="button">Sign in with Twitter</a>
                <a href="/api/auth/twitter/status" class="button button-secondary" style="margin-top:10px; display:inline-block">Check Status</a>
            </div>

            <div class="card">
                <h2>📝 Tweet Management</h2>
                <p>Create, schedule, and manage your tweets with ease. Support for both manual and AI-generated content.</p>
                <a href="/docs#/tweets" class="button">Manage Tweets</a>
            </div>

            <div class="card">
                <h2>🤖 AI Generation</h2>
                <p>Generate engaging tweets using Azure OpenAI. Customize style, tone, and topics to match your brand.</p>
                <a href="/docs#/ai" class="button button-secondary">Generate Content</a>
            </div>

            <div class="card">
                <h2>📊 Analytics</h2>
                <p>Track your tweet performance with detailed analytics. Monitor engagement, reach, and trends.</p>
                <a href="/docs#/analytics" class="button">View Analytics</a>
            </div>
        </div>

        <div class="api-docs">
            <h2>🚀 Quick Start - API Endpoints</h2>

            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/auth/twitter/login</code>
                <p>Authenticate with Twitter (OAuth 2.0)</p>
            </div>

            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/tweets/</code>
                <p>Create a new tweet (manual or scheduled)</p>
            </div>

            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/ai/generate</code>
                <p>Generate tweets using AI</p>
            </div>

            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/tweets/</code>
                <p>Get list of all tweets (with filtering options)</p>
            </div>

            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/tweets/{id}/post</code>
                <p>Post a tweet immediately</p>
            </div>

            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/tweets/{id}/approve</code>
                <p>Approve an AI-generated tweet</p>
            </div>

            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/analytics/summary</code>
                <p>Get analytics summary</p>
            </div>

            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/analytics/top-tweets</code>
                <p>Get top performing tweets</p>
            </div>

            <p style="margin-top: 20px;">
                <a href="/docs" class="button">📚 Full API Documentation</a>
                <a href="/health" class="button button-secondary">🏥 Health Check</a>
            </p>
        </div>

        <div class="footer">
            <p>Built with FastAPI, Azure OpenAI, and ❤️</p>
            <p>Version 0.1.0</p>
        </div>
    </div>
</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False,
    )
