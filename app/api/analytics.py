"""Analytics API endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Tweet, TweetStatus, ActivityLog
from app.schemas import AnalyticsResponse, ActivityLogResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsResponse)
def get_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get analytics summary for the specified period"""

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Total tweets
    total_tweets = db.query(func.count(Tweet.id)).filter(
        Tweet.created_at >= start_date
    ).scalar()

    # Tweets by status
    posted_tweets = db.query(func.count(Tweet.id)).filter(
        Tweet.status == TweetStatus.POSTED,
        Tweet.created_at >= start_date
    ).scalar()

    scheduled_tweets = db.query(func.count(Tweet.id)).filter(
        Tweet.status == TweetStatus.SCHEDULED
    ).scalar()

    draft_tweets = db.query(func.count(Tweet.id)).filter(
        Tweet.status == TweetStatus.DRAFT
    ).scalar()

    failed_tweets = db.query(func.count(Tweet.id)).filter(
        Tweet.status == TweetStatus.FAILED,
        Tweet.created_at >= start_date
    ).scalar()

    # Engagement metrics
    engagement_stats = db.query(
        func.sum(Tweet.likes_count).label("total_likes"),
        func.sum(Tweet.retweets_count).label("total_retweets"),
        func.sum(Tweet.replies_count).label("total_replies"),
        func.sum(Tweet.impressions_count).label("total_impressions"),
    ).filter(
        Tweet.status == TweetStatus.POSTED,
        Tweet.posted_time >= start_date
    ).first()

    total_likes = engagement_stats.total_likes or 0
    total_retweets = engagement_stats.total_retweets or 0
    total_replies = engagement_stats.total_replies or 0
    total_impressions = engagement_stats.total_impressions or 0

    # Calculate average engagement rate
    if posted_tweets > 0 and total_impressions > 0:
        total_engagements = total_likes + total_retweets + total_replies
        avg_engagement_rate = (total_engagements / total_impressions) * 100
    else:
        avg_engagement_rate = 0.0

    return AnalyticsResponse(
        total_tweets=total_tweets,
        posted_tweets=posted_tweets,
        scheduled_tweets=scheduled_tweets,
        draft_tweets=draft_tweets,
        failed_tweets=failed_tweets,
        total_likes=total_likes,
        total_retweets=total_retweets,
        total_replies=total_replies,
        total_impressions=total_impressions,
        avg_engagement_rate=round(avg_engagement_rate, 2),
    )


@router.get("/activity-log", response_model=List[ActivityLogResponse])
def get_activity_log(
    action: str = Query(None),
    success: bool = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get activity log with optional filtering"""
    query = db.query(ActivityLog)

    if action:
        query = query.filter(ActivityLog.action == action)
    if success is not None:
        query = query.filter(ActivityLog.success == success)

    logs = query.order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/top-tweets", response_model=List)
def get_top_tweets(
    metric: str = Query("likes", regex="^(likes|retweets|replies|impressions)$"),
    limit: int = Query(10, ge=1, le=100),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get top performing tweets based on specified metric"""

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Map metric to column
    metric_column_map = {
        "likes": Tweet.likes_count,
        "retweets": Tweet.retweets_count,
        "replies": Tweet.replies_count,
        "impressions": Tweet.impressions_count,
    }

    metric_column = metric_column_map[metric]

    tweets = (
        db.query(Tweet)
        .filter(
            Tweet.status == TweetStatus.POSTED,
            Tweet.posted_time >= start_date
        )
        .order_by(metric_column.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": tweet.id,
            "content": tweet.content,
            "posted_time": tweet.posted_time,
            "twitter_url": tweet.twitter_url,
            "likes": tweet.likes_count,
            "retweets": tweet.retweets_count,
            "replies": tweet.replies_count,
            "impressions": tweet.impressions_count,
        }
        for tweet in tweets
    ]
