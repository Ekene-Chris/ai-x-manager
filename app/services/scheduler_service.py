"""Scheduler service for automated tweet posting"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import SessionLocal
from app.models import Tweet, TweetStatus, ActivityLog, TwitterAuth

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling and posting tweets"""

    def __init__(self):
        """Initialize scheduler"""
        self.scheduler = BackgroundScheduler(timezone=timezone.utc)
        logger.info("Scheduler service initialized")

    def _get_twitter_client(self, db: Session):
        """Get Twitter client using OAuth"""
        try:
            # Import here to avoid circular dependency
            from app.services.twitter_oauth_service import TwitterOAuthService

            # Get OAuth authentication from database
            auth = db.query(TwitterAuth).filter(TwitterAuth.is_active == True).first()
            if not auth or not auth.access_token:
                logger.error("No active Twitter authentication found")
                return None

            # Create Tweepy client with OAuth token
            import tweepy
            client = tweepy.Client(
                bearer_token=auth.access_token,
                wait_on_rate_limit=True,
            )
            return client

        except Exception as e:
            logger.error(f"Error getting Twitter client: {str(e)}")
            return None

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
            # Load any existing scheduled tweets
            self.load_scheduled_tweets()

    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")

    def schedule_tweet(self, tweet_id: int, scheduled_time: datetime) -> bool:
        """
        Schedule a tweet for posting

        Args:
            tweet_id: Database ID of the tweet
            scheduled_time: When to post the tweet

        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            # Remove existing job if any
            job_id = f"tweet_{tweet_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)

            # Schedule new job
            self.scheduler.add_job(
                func=self._post_scheduled_tweet,
                trigger=DateTrigger(run_date=scheduled_time),
                args=[tweet_id],
                id=job_id,
                name=f"Post tweet {tweet_id}",
                replace_existing=True,
            )

            logger.info(f"Tweet {tweet_id} scheduled for {scheduled_time}")
            return True

        except Exception as e:
            logger.error(f"Error scheduling tweet {tweet_id}: {str(e)}")
            return False

    def cancel_scheduled_tweet(self, tweet_id: int) -> bool:
        """
        Cancel a scheduled tweet

        Args:
            tweet_id: Database ID of the tweet

        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            job_id = f"tweet_{tweet_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"Cancelled scheduled tweet {tweet_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling tweet {tweet_id}: {str(e)}")
            return False

    def reschedule_tweet(self, tweet_id: int, new_time: datetime) -> bool:
        """
        Reschedule a tweet to a new time

        Args:
            tweet_id: Database ID of the tweet
            new_time: New scheduled time

        Returns:
            True if rescheduled successfully, False otherwise
        """
        return self.schedule_tweet(tweet_id, new_time)

    def load_scheduled_tweets(self):
        """Load all scheduled tweets from database and schedule them"""
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            scheduled_tweets = (
                db.query(Tweet)
                .filter(
                    Tweet.status == TweetStatus.SCHEDULED,
                    Tweet.scheduled_time > now,
                )
                .all()
            )

            count = 0
            for tweet in scheduled_tweets:
                if self.schedule_tweet(tweet.id, tweet.scheduled_time):
                    count += 1

            logger.info(f"Loaded {count} scheduled tweets")

        except Exception as e:
            logger.error(f"Error loading scheduled tweets: {str(e)}")
        finally:
            db.close()

    def _post_scheduled_tweet(self, tweet_id: int):
        """
        Internal method to post a scheduled tweet

        Args:
            tweet_id: Database ID of the tweet
        """
        db = SessionLocal()
        try:
            # Get tweet from database
            tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()

            if not tweet:
                logger.error(f"Tweet {tweet_id} not found in database")
                return

            if tweet.status != TweetStatus.SCHEDULED:
                logger.warning(f"Tweet {tweet_id} is not in SCHEDULED status, skipping")
                return

            # Get Twitter client
            client = self._get_twitter_client(db)
            if not client:
                raise Exception("Twitter client not available - please authenticate")

            # Post to Twitter
            logger.info(f"Posting scheduled tweet {tweet_id}: {tweet.content[:50]}...")
            response = client.create_tweet(text=tweet.content)

            if response.data:
                tweet_id_str = response.data["id"]
                tweet_url = f"https://twitter.com/i/web/status/{tweet_id_str}"

                # Update tweet in database
                tweet.status = TweetStatus.POSTED
                tweet.twitter_id = tweet_id_str
                tweet.twitter_url = tweet_url
                tweet.posted_time = datetime.now(timezone.utc)
                tweet.error_message = None

                # Log activity
                activity = ActivityLog(
                    action="tweet_posted",
                    description=f"Scheduled tweet posted successfully",
                    tweet_id=tweet_id,
                    success=True,
                    extra_data=str(response.data),
                )
                db.add(activity)

                logger.info(f"Tweet {tweet_id} posted successfully: {tweet_url}")
            else:
                # Mark as failed
                tweet.status = TweetStatus.FAILED
                tweet.error_message = "Failed to post to Twitter - no response data"
                tweet.retry_count += 1

                # Log activity
                activity = ActivityLog(
                    action="tweet_post_failed",
                    description="Failed to post scheduled tweet",
                    tweet_id=tweet_id,
                    success=False,
                    error_message="Failed to post to Twitter - no response data",
                )
                db.add(activity)

                logger.error(f"Failed to post tweet {tweet_id}")

            db.commit()

        except Exception as e:
            logger.error(f"Error posting scheduled tweet {tweet_id}: {str(e)}")
            db.rollback()

            # Update tweet status to failed
            try:
                tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
                if tweet:
                    tweet.status = TweetStatus.FAILED
                    tweet.error_message = str(e)
                    tweet.retry_count += 1

                    activity = ActivityLog(
                        action="tweet_post_failed",
                        description="Error posting scheduled tweet",
                        tweet_id=tweet_id,
                        success=False,
                        error_message=str(e),
                    )
                    db.add(activity)
                    db.commit()
            except Exception as inner_e:
                logger.error(f"Error updating tweet status: {str(inner_e)}")
                db.rollback()

        finally:
            db.close()

    def post_tweet_now(self, tweet_id: int) -> bool:
        """
        Post a tweet immediately (bypass scheduling)

        Args:
            tweet_id: Database ID of the tweet

        Returns:
            True if posted successfully, False otherwise
        """
        try:
            self._post_scheduled_tweet(tweet_id)
            return True
        except Exception as e:
            logger.error(f"Error posting tweet immediately: {str(e)}")
            return False

    def get_scheduled_jobs(self) -> list:
        """
        Get list of all scheduled jobs

        Returns:
            List of job information dictionaries
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time,
                }
            )
        return jobs
