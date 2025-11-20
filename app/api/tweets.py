"""Tweet management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models import Tweet, TweetStatus, TweetSource, ActivityLog
from app.schemas import TweetCreate, TweetUpdate, TweetResponse
from app.services.scheduler_service import SchedulerService
from app.services.twitter_service import TwitterService

router = APIRouter(prefix="/tweets", tags=["tweets"])

# Global instances (will be initialized in main.py)
scheduler_service: Optional[SchedulerService] = None
twitter_service: Optional[TwitterService] = None


def set_services(scheduler: SchedulerService, twitter: TwitterService):
    """Set service instances"""
    global scheduler_service, twitter_service
    scheduler_service = scheduler
    twitter_service = twitter


@router.get("/", response_model=List[TweetResponse])
def get_tweets(
    status: Optional[TweetStatus] = None,
    source: Optional[TweetSource] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get list of tweets with optional filtering"""
    query = db.query(Tweet)

    if status:
        query = query.filter(Tweet.status == status)
    if source:
        query = query.filter(Tweet.source == source)

    tweets = query.order_by(Tweet.created_at.desc()).offset(skip).limit(limit).all()
    return tweets


@router.get("/{tweet_id}", response_model=TweetResponse)
def get_tweet(tweet_id: int, db: Session = Depends(get_db)):
    """Get a specific tweet by ID"""
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    return tweet


@router.post("/", response_model=TweetResponse, status_code=201)
def create_tweet(tweet: TweetCreate, db: Session = Depends(get_db)):
    """Create a new tweet"""
    # Determine initial status
    if tweet.scheduled_time:
        if tweet.scheduled_time <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="Scheduled time must be in the future",
            )
        status = TweetStatus.SCHEDULED
    else:
        status = TweetStatus.DRAFT

    # Create tweet
    db_tweet = Tweet(
        content=tweet.content,
        status=status,
        source=tweet.source,
        scheduled_time=tweet.scheduled_time,
    )
    db.add(db_tweet)
    db.commit()
    db.refresh(db_tweet)

    # Schedule if needed
    if status == TweetStatus.SCHEDULED and scheduler_service:
        scheduler_service.schedule_tweet(db_tweet.id, tweet.scheduled_time)

    # Log activity
    activity = ActivityLog(
        action="tweet_created",
        description=f"Tweet created with status {status}",
        tweet_id=db_tweet.id,
        success=True,
    )
    db.add(activity)
    db.commit()

    return db_tweet


@router.put("/{tweet_id}", response_model=TweetResponse)
def update_tweet(tweet_id: int, tweet_update: TweetUpdate, db: Session = Depends(get_db)):
    """Update an existing tweet"""
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    # Check if tweet can be updated
    if db_tweet.status == TweetStatus.POSTED:
        raise HTTPException(status_code=400, detail="Cannot update posted tweets")

    # Update fields
    if tweet_update.content is not None:
        db_tweet.content = tweet_update.content

    if tweet_update.status is not None:
        old_status = db_tweet.status
        db_tweet.status = tweet_update.status

        # Handle status transitions
        if tweet_update.status == TweetStatus.SCHEDULED and old_status != TweetStatus.SCHEDULED:
            if not tweet_update.scheduled_time and not db_tweet.scheduled_time:
                raise HTTPException(
                    status_code=400,
                    detail="Must provide scheduled_time when changing status to SCHEDULED",
                )

    if tweet_update.scheduled_time is not None:
        if tweet_update.scheduled_time <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="Scheduled time must be in the future",
            )
        db_tweet.scheduled_time = tweet_update.scheduled_time
        db_tweet.status = TweetStatus.SCHEDULED

        # Reschedule
        if scheduler_service:
            scheduler_service.reschedule_tweet(tweet_id, tweet_update.scheduled_time)

    db.commit()
    db.refresh(db_tweet)

    return db_tweet


@router.delete("/{tweet_id}", status_code=204)
def delete_tweet(tweet_id: int, db: Session = Depends(get_db)):
    """Delete a tweet"""
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    # Cancel scheduled job if exists
    if db_tweet.status == TweetStatus.SCHEDULED and scheduler_service:
        scheduler_service.cancel_scheduled_tweet(tweet_id)

    # Delete from Twitter if posted
    if db_tweet.status == TweetStatus.POSTED and db_tweet.twitter_id and twitter_service:
        twitter_service.delete_tweet(db_tweet.twitter_id)

    db.delete(db_tweet)
    db.commit()

    return None


@router.post("/{tweet_id}/post", response_model=TweetResponse)
def post_tweet_now(tweet_id: int, db: Session = Depends(get_db)):
    """Post a tweet immediately"""
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if db_tweet.status == TweetStatus.POSTED:
        raise HTTPException(status_code=400, detail="Tweet already posted")

    if not twitter_service:
        raise HTTPException(status_code=500, detail="Twitter service not available")

    try:
        # Post to Twitter
        result = twitter_service.post_tweet(db_tweet.content)

        if result:
            db_tweet.status = TweetStatus.POSTED
            db_tweet.twitter_id = result["id"]
            db_tweet.twitter_url = result["url"]
            db_tweet.posted_time = datetime.now(timezone.utc)
            db_tweet.error_message = None

            # Cancel scheduled job if exists
            if scheduler_service:
                scheduler_service.cancel_scheduled_tweet(tweet_id)

            # Log activity
            activity = ActivityLog(
                action="tweet_posted",
                description="Tweet posted manually",
                tweet_id=tweet_id,
                success=True,
            )
            db.add(activity)

            db.commit()
            db.refresh(db_tweet)

            return db_tweet
        else:
            raise HTTPException(status_code=500, detail="Failed to post tweet")

    except Exception as e:
        db_tweet.status = TweetStatus.FAILED
        db_tweet.error_message = str(e)
        db_tweet.retry_count += 1

        activity = ActivityLog(
            action="tweet_post_failed",
            description="Failed to post tweet manually",
            tweet_id=tweet_id,
            success=False,
            error_message=str(e),
        )
        db.add(activity)

        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tweet_id}/approve", response_model=TweetResponse)
def approve_tweet(tweet_id: int, db: Session = Depends(get_db)):
    """Approve an AI-generated tweet"""
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if db_tweet.status != TweetStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft tweets can be approved")

    db_tweet.status = TweetStatus.APPROVED

    activity = ActivityLog(
        action="tweet_approved",
        description="AI-generated tweet approved",
        tweet_id=tweet_id,
        success=True,
    )
    db.add(activity)

    db.commit()
    db.refresh(db_tweet)

    return db_tweet


@router.post("/{tweet_id}/reject", response_model=TweetResponse)
def reject_tweet(tweet_id: int, db: Session = Depends(get_db)):
    """Reject an AI-generated tweet"""
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if db_tweet.status != TweetStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft tweets can be rejected")

    db_tweet.status = TweetStatus.REJECTED

    activity = ActivityLog(
        action="tweet_rejected",
        description="AI-generated tweet rejected",
        tweet_id=tweet_id,
        success=True,
    )
    db.add(activity)

    db.commit()
    db.refresh(db_tweet)

    return db_tweet


@router.get("/{tweet_id}/metrics", response_model=TweetResponse)
def refresh_tweet_metrics(tweet_id: int, db: Session = Depends(get_db)):
    """Refresh engagement metrics for a posted tweet"""
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if db_tweet.status != TweetStatus.POSTED or not db_tweet.twitter_id:
        raise HTTPException(status_code=400, detail="Tweet must be posted to fetch metrics")

    if not twitter_service:
        raise HTTPException(status_code=500, detail="Twitter service not available")

    # Fetch metrics from Twitter
    metrics = twitter_service.get_tweet_metrics(db_tweet.twitter_id)

    if metrics:
        db_tweet.likes_count = metrics["likes"]
        db_tweet.retweets_count = metrics["retweets"]
        db_tweet.replies_count = metrics["replies"]
        db_tweet.impressions_count = metrics["impressions"]

        db.commit()
        db.refresh(db_tweet)

    return db_tweet
