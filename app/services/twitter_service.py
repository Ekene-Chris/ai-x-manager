"""Twitter API service for posting tweets and managing interactions"""

import tweepy
from typing import Optional, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class TwitterService:
    """Service for interacting with X (Twitter) API"""

    def __init__(self):
        """Initialize Twitter API client"""
        try:
            # Authenticate to Twitter using API v2
            self.client = tweepy.Client(
                bearer_token=settings.twitter_bearer_token,
                consumer_key=settings.twitter_api_key,
                consumer_secret=settings.twitter_api_secret,
                access_token=settings.twitter_access_token,
                access_token_secret=settings.twitter_access_token_secret,
                wait_on_rate_limit=True,
            )
            logger.info("Twitter API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twitter API client: {str(e)}")
            raise

    def post_tweet(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Post a tweet to Twitter

        Args:
            text: Tweet content (max 280 characters)

        Returns:
            Dictionary with tweet ID and URL if successful, None otherwise
        """
        try:
            if len(text) > 280:
                logger.warning(f"Tweet text exceeds 280 characters: {len(text)}")
                raise ValueError("Tweet text must be 280 characters or less")

            # Post tweet
            response = self.client.create_tweet(text=text)

            if response.data:
                tweet_id = response.data["id"]
                tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"

                logger.info(f"Tweet posted successfully: {tweet_id}")
                return {
                    "id": tweet_id,
                    "url": tweet_url,
                    "text": text,
                }
            else:
                logger.error("Failed to post tweet: No data in response")
                return None

        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error while posting tweet: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while posting tweet: {str(e)}")
            raise

    def delete_tweet(self, tweet_id: str) -> bool:
        """
        Delete a tweet

        Args:
            tweet_id: Twitter tweet ID

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.client.delete_tweet(tweet_id)
            logger.info(f"Tweet deleted successfully: {tweet_id}")
            return response.data.get("deleted", False)
        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error while deleting tweet: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while deleting tweet: {str(e)}")
            return False

    def get_tweet_metrics(self, tweet_id: str) -> Optional[Dict[str, int]]:
        """
        Get engagement metrics for a tweet

        Args:
            tweet_id: Twitter tweet ID

        Returns:
            Dictionary with engagement metrics
        """
        try:
            tweet = self.client.get_tweet(
                tweet_id,
                tweet_fields=["public_metrics"],
            )

            if tweet.data:
                metrics = tweet.data.public_metrics
                return {
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                    "impressions": metrics.get("impression_count", 0),
                }
            return None

        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error while getting metrics: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while getting metrics: {str(e)}")
            return None

    def get_mentions(self, since_id: Optional[str] = None, max_results: int = 10) -> list:
        """
        Get mentions of the authenticated user

        Args:
            since_id: Get tweets since this tweet ID
            max_results: Maximum number of results (default 10, max 100)

        Returns:
            List of mention tweets
        """
        try:
            # Get authenticated user's ID
            me = self.client.get_me()
            if not me.data:
                logger.error("Failed to get authenticated user information")
                return []

            user_id = me.data.id

            # Get mentions
            mentions = self.client.get_users_mentions(
                user_id,
                since_id=since_id,
                max_results=max_results,
                tweet_fields=["created_at", "author_id", "conversation_id"],
            )

            if mentions.data:
                return [
                    {
                        "id": tweet.id,
                        "text": tweet.text,
                        "author_id": tweet.author_id,
                        "created_at": tweet.created_at,
                        "conversation_id": tweet.conversation_id,
                    }
                    for tweet in mentions.data
                ]
            return []

        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error while getting mentions: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while getting mentions: {str(e)}")
            return []

    def reply_to_tweet(self, tweet_id: str, text: str) -> Optional[Dict[str, Any]]:
        """
        Reply to a tweet

        Args:
            tweet_id: ID of tweet to reply to
            text: Reply content

        Returns:
            Dictionary with reply tweet information
        """
        try:
            response = self.client.create_tweet(
                text=text,
                in_reply_to_tweet_id=tweet_id,
            )

            if response.data:
                reply_id = response.data["id"]
                logger.info(f"Reply posted successfully: {reply_id}")
                return {
                    "id": reply_id,
                    "text": text,
                    "in_reply_to": tweet_id,
                }
            return None

        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error while replying to tweet: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while replying to tweet: {str(e)}")
            raise

    def verify_credentials(self) -> bool:
        """
        Verify that API credentials are valid

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            me = self.client.get_me()
            if me.data:
                logger.info(f"Credentials verified for user: @{me.data.username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to verify credentials: {str(e)}")
            return False
