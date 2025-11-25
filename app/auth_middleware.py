"""Authentication middleware for web dashboard"""

from fastapi import Request, HTTPException, status
from fastapi.responses import HTMLResponse
from typing import Optional
import secrets
import base64
from app.config import settings


class BasicAuthMiddleware:
    """Simple basic authentication for the web dashboard"""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

    def verify_credentials(self, authorization: Optional[str]) -> bool:
        """Verify basic auth credentials"""
        if not authorization:
            return False

        try:
            scheme, credentials = authorization.split()
            if scheme.lower() != "basic":
                return False

            return credentials == self.credentials
        except Exception:
            return False

    def get_auth_response(self) -> HTMLResponse:
        """Return 401 response with auth challenge"""
        return HTMLResponse(
            content="""
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Required</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        h1 { color: #1DA1F2; margin-bottom: 20px; }
        p { color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Authentication Required</h1>
        <p>Please sign in to access the AI X Account Manager dashboard.</p>
    </div>
</body>
</html>
            """,
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="AI X Account Manager"'},
        )


# Initialize middleware if credentials are set
auth_middleware: Optional[BasicAuthMiddleware] = None

if settings.dashboard_username and settings.dashboard_password:
    auth_middleware = BasicAuthMiddleware(
        settings.dashboard_username,
        settings.dashboard_password,
    )


def check_dashboard_auth(request: Request) -> bool:
    """
    Check if request is authenticated for dashboard access

    Returns:
        True if authenticated or auth not enabled, False otherwise
    """
    if not auth_middleware:
        # Auth not configured, allow access
        return True

    authorization = request.headers.get("Authorization")
    return auth_middleware.verify_credentials(authorization)


def require_dashboard_auth(request: Request):
    """
    Require authentication for dashboard access

    Raises:
        HTTPException: If authentication fails
    """
    if not check_dashboard_auth(request):
        if auth_middleware:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": 'Basic realm="AI X Account Manager"'},
            )
