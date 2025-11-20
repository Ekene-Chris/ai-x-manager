"""Authentication API endpoints for Twitter OAuth"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.services.twitter_oauth_service import TwitterOAuthService
from app.models import ActivityLog

router = APIRouter(prefix="/auth/twitter", tags=["authentication"])

# Global OAuth service instance
oauth_service: TwitterOAuthService = None


def set_oauth_service(service: TwitterOAuthService):
    """Set OAuth service instance"""
    global oauth_service
    oauth_service = service


@router.get("/login")
def twitter_login():
    """
    Initiate Twitter OAuth login flow

    Returns authorization URL for user to visit
    """
    if not oauth_service:
        raise HTTPException(
            status_code=500,
            detail="OAuth service not configured. Please set TWITTER_CLIENT_ID and TWITTER_CLIENT_SECRET in .env",
        )

    try:
        result = oauth_service.get_authorization_url()

        # Return HTML page with redirect
        return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Authenticate with Twitter</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 500px;
        }}
        h1 {{
            color: #1DA1F2;
            margin-bottom: 20px;
        }}
        p {{
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
        }}
        .button {{
            display: inline-block;
            background: #1DA1F2;
            color: white;
            padding: 15px 30px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        .button:hover {{
            background: #1a91da;
            transform: scale(1.05);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🐦 Connect Your Twitter Account</h1>
        <p>Click the button below to authenticate with Twitter and authorize AI X Account Manager to post tweets on your behalf.</p>
        <a href="{result['authorization_url']}" class="button">Authenticate with Twitter</a>
    </div>
</body>
</html>
        """)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
def twitter_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    Handle Twitter OAuth callback

    This endpoint is called by Twitter after user authorizes the app
    """
    if error:
        return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Failed</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 500px;
        }}
        h1 {{
            color: #f93e3e;
            margin-bottom: 20px;
        }}
        p {{
            color: #666;
            margin-bottom: 30px;
        }}
        .button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 15px 30px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>❌ Authentication Failed</h1>
        <p>Error: {error}</p>
        <a href="/api/auth/twitter/login" class="button">Try Again</a>
    </div>
</body>
</html>
        """)

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")

    if not oauth_service:
        raise HTTPException(status_code=500, detail="OAuth service not configured")

    try:
        # Build the full callback URL
        from fastapi import Request
        from starlette.requests import Request as StarletteRequest

        # Get the current request to build full callback URL
        authorization_response = f"http://localhost:8000/api/auth/twitter/callback?code={code}&state={state}"

        # Handle the callback
        result = oauth_service.handle_callback(authorization_response, db)

        # Log successful authentication
        activity = ActivityLog(
            action="twitter_authenticated",
            description=f"User @{result['user']['username']} authenticated successfully",
            success=True,
        )
        db.add(activity)
        db.commit()

        # Return success page
        return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Successful</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 500px;
        }}
        h1 {{
            color: #49cc90;
            margin-bottom: 20px;
        }}
        .user-info {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .user-info p {{
            margin: 5px 0;
            color: #333;
        }}
        .button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 15px 30px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Successfully Authenticated!</h1>
        <p>Your Twitter account has been connected to AI X Account Manager.</p>
        <div class="user-info">
            <p><strong>Username:</strong> @{result['user']['username']}</p>
            <p><strong>Name:</strong> {result['user']['name']}</p>
        </div>
        <p>You can now close this window and use the API to manage your tweets.</p>
        <a href="/" class="button">Go to Dashboard</a>
    </div>
</body>
</html>
        """)

    except Exception as e:
        activity = ActivityLog(
            action="twitter_auth_failed",
            description="Twitter authentication failed",
            success=False,
            error_message=str(e),
        )
        db.add(activity)
        db.commit()

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def get_auth_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get current authentication status"""
    if not oauth_service:
        return {
            "authenticated": False,
            "message": "OAuth service not configured",
        }

    return oauth_service.get_auth_status(db)


@router.post("/logout")
def logout(db: Session = Depends(get_db)):
    """Logout and revoke Twitter access"""
    if not oauth_service:
        raise HTTPException(status_code=500, detail="OAuth service not configured")

    success = oauth_service.revoke_access(db)

    if success:
        activity = ActivityLog(
            action="twitter_logout",
            description="User logged out and revoked Twitter access",
            success=True,
        )
        db.add(activity)
        db.commit()

        return {"message": "Successfully logged out"}
    else:
        raise HTTPException(status_code=400, detail="No active session to logout")
