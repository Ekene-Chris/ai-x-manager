"""Twitter OAuth 2.0 service for user authentication"""

import tweepy
from tweepy import OAuth2UserHandler
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import os

from app.config import settings
from app.models import TwitterAuth

logger = logging.getLogger(__name__)

# Allow OAuth over HTTP when behind a secure reverse proxy (Azure Container Apps, etc.)
# The external traffic is HTTPS, but internal container communication might be HTTP
if settings.environment == "production":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    logger.info("OAuth insecure transport enabled for production (behind secure proxy)")


class TwitterOAuthService:
    """Service for Twitter OAuth 2.0 authentication and API access"""

    def __init__(self):
        """Initialize OAuth handler"""
        self.client_id = settings.twitter_client_id
        self.client_secret = settings.twitter_client_secret
        self.redirect_uri = settings.twitter_redirect_uri

        # Ensure HTTPS in production for security
        if settings.environment == "production" and self.redirect_uri.startswith("http://"):
            logger.warning(f"Redirect URI uses HTTP in production: {self.redirect_uri}")
            logger.warning("Consider updating TWITTER_REDIRECT_URI to use HTTPS")

        self.oauth2_user_handler = None
        self._init_oauth_handler()

    def _init_oauth_handler(self):
        """Initialize OAuth 2.0 user handler"""
        try:
            self.oauth2_user_handler = OAuth2UserHandler(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=["tweet.read", "tweet.write", "users.read", "offline.access"],
                client_secret=self.client_secret,
            )
            logger.info("OAuth2 handler initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OAuth2 handler: {str(e)}")
            raise

    def get_authorization_url(self) -> Dict[str, str]:
        """
        Get the authorization URL for user to authenticate

        Returns:
            Dictionary with authorization URL and state
        """
        try:
            auth_url = self.oauth2_user_handler.get_authorization_url()
            logger.info("Generated authorization URL")
            return {
                "authorization_url": auth_url,
                "message": "Please visit the authorization_url to authenticate with Twitter",
            }
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise

    def handle_callback(
        self, authorization_response: str, db: Session
    ) -> Dict[str, Any]:
        """
        Handle OAuth callback and store tokens

        Args:
            authorization_response: Full callback URL with code
            db: Database session

        Returns:
            Dictionary with success status and user info
        """
        try:
            # Exchange authorization code for access token
            access_token = self.oauth2_user_handler.fetch_token(authorization_response)

            # Create client with access token
            client = tweepy.Client(
                bearer_token=access_token["access_token"],
                wait_on_rate_limit=True,
            )

            # Get user info
            me = client.get_me()
            if not me.data:
                raise Exception("Failed to get user information")

            user_info = {
                "id": str(me.data.id),
                "username": me.data.username,
                "name": me.data.name,
            }

            # Store tokens in database
            twitter_auth = db.query(TwitterAuth).first()
            if twitter_auth:
                # Update existing
                twitter_auth.access_token = access_token["access_token"]
                twitter_auth.refresh_token = access_token.get("refresh_token")
                twitter_auth.token_expires_at = datetime.fromtimestamp(
                    access_token["expires_at"], tz=timezone.utc
                )
                twitter_auth.twitter_user_id = user_info["id"]
                twitter_auth.twitter_username = user_info["username"]
                twitter_auth.twitter_name = user_info["name"]
                twitter_auth.is_active = True
            else:
                # Create new
                twitter_auth = TwitterAuth(
                    access_token=access_token["access_token"],
                    refresh_token=access_token.get("refresh_token"),
                    token_expires_at=datetime.fromtimestamp(
                        access_token["expires_at"], tz=timezone.utc
                    ),
                    twitter_user_id=user_info["id"],
                    twitter_username=user_info["username"],
                    twitter_name=user_info["name"],
                    is_active=True,
                )
                db.add(twitter_auth)

            db.commit()
            logger.info(f"OAuth tokens stored for user: @{user_info['username']}")

            return {
                "success": True,
                "user": user_info,
                "message": "Successfully authenticated with Twitter!",
            }

        except Exception as e:
            logger.error(f"Error handling OAuth callback: {str(e)}")
            db.rollback()
            raise

    def get_client(self, db: Session) -> Optional[tweepy.Client]:
        """
        Get authenticated Twitter client

        Args:
            db: Database session

        Returns:
            Authenticated tweepy Client or None
        """
        try:
            auth = db.query(TwitterAuth).filter(TwitterAuth.is_active == True).first()
            if not auth:
                logger.warning("No active Twitter authentication found")
                return None

            # Check if token needs refresh
            if auth.token_expires_at and auth.token_expires_at <= datetime.now(
                timezone.utc
            ):
                logger.info("Access token expired, refreshing...")
                auth = self.refresh_access_token(auth, db)

            if not auth or not auth.access_token:
                return None

            # Create client with access token
            client = tweepy.Client(
                bearer_token=auth.access_token,
                wait_on_rate_limit=True,
            )

            return client

        except Exception as e:
            logger.error(f"Error getting Twitter client: {str(e)}")
            return None

    def refresh_access_token(
        self, auth: TwitterAuth, db: Session
    ) -> Optional[TwitterAuth]:
        """
        Refresh expired access token

        Args:
            auth: TwitterAuth object with refresh token
            db: Database session

        Returns:
            Updated TwitterAuth object or None
        """
        try:
            if not auth.refresh_token:
                logger.error("No refresh token available")
                return None

            # Refresh token
            new_token = self.oauth2_user_handler.refresh_token(
                f"https://api.twitter.com/2/oauth2/token",
                refresh_token=auth.refresh_token,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            # Update tokens
            auth.access_token = new_token["access_token"]
            auth.refresh_token = new_token.get("refresh_token", auth.refresh_token)
            auth.token_expires_at = datetime.fromtimestamp(
                new_token["expires_at"], tz=timezone.utc
            )

            db.commit()
            logger.info("Access token refreshed successfully")
            return auth

        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            db.rollback()
            return None

    def is_authenticated(self, db: Session) -> bool:
        """
        Check if user is authenticated

        Args:
            db: Database session

        Returns:
            True if authenticated, False otherwise
        """
        auth = db.query(TwitterAuth).filter(TwitterAuth.is_active == True).first()
        return auth is not None and auth.access_token is not None

    def get_auth_status(self, db: Session) -> Dict[str, Any]:
        """
        Get authentication status

        Args:
            db: Database session

        Returns:
            Dictionary with auth status and user info
        """
        auth = db.query(TwitterAuth).filter(TwitterAuth.is_active == True).first()

        if not auth:
            return {
                "authenticated": False,
                "message": "Not authenticated. Please authenticate with Twitter.",
            }

        return {
            "authenticated": True,
            "user": {
                "id": auth.twitter_user_id,
                "username": auth.twitter_username,
                "name": auth.twitter_name,
            },
            "token_expires_at": auth.token_expires_at.isoformat()
            if auth.token_expires_at
            else None,
        }

    def revoke_access(self, db: Session) -> bool:
        """
        Revoke access and delete tokens

        Args:
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            auth = db.query(TwitterAuth).filter(TwitterAuth.is_active == True).first()
            if auth:
                auth.is_active = False
                auth.access_token = None
                auth.refresh_token = None
                db.commit()
                logger.info("Twitter access revoked")
                return True
            return False
        except Exception as e:
            logger.error(f"Error revoking access: {str(e)}")
            db.rollback()
            return False
