"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import TweetStatus, TweetSource


# Tweet schemas
class TweetCreate(BaseModel):
    """Schema for creating a new tweet"""
    content: str = Field(..., max_length=280, description="Tweet content")
    scheduled_time: Optional[datetime] = Field(None, description="When to post the tweet")
    source: TweetSource = Field(default=TweetSource.MANUAL, description="Source of the tweet")


class TweetUpdate(BaseModel):
    """Schema for updating a tweet"""
    content: Optional[str] = Field(None, max_length=280)
    scheduled_time: Optional[datetime] = None
    status: Optional[TweetStatus] = None


class TweetResponse(BaseModel):
    """Schema for tweet response"""
    id: int
    content: str
    status: TweetStatus
    source: TweetSource
    scheduled_time: Optional[datetime] = None
    posted_time: Optional[datetime] = None
    twitter_id: Optional[str] = None
    twitter_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    ai_prompt: Optional[str] = None
    ai_model: Optional[str] = None
    likes_count: int
    retweets_count: int
    replies_count: int
    impressions_count: int

    class Config:
        from_attributes = True


# AI Generation schemas
class AITweetGenerateRequest(BaseModel):
    """Schema for AI tweet generation request"""
    topic: Optional[str] = Field(None, description="Topic for the tweet")
    style: str = Field(default="professional", description="Writing style")
    tone: str = Field(default="engaging", description="Tone of the tweet")
    context: Optional[str] = Field(None, description="Additional context")
    count: int = Field(default=1, ge=1, le=10, description="Number of tweets to generate")


class AITweetImproveRequest(BaseModel):
    """Schema for AI tweet improvement request"""
    tweet_id: int
    improvement_type: str = Field(default="engagement", description="Type of improvement")


class AIReplyGenerateRequest(BaseModel):
    """Schema for AI reply generation request"""
    original_tweet: str
    reply_type: str = Field(default="friendly", description="Type of reply")
    context: Optional[str] = None


# User Preference schemas
class PreferenceCreate(BaseModel):
    """Schema for creating a preference"""
    key: str
    value: str
    description: Optional[str] = None


class PreferenceResponse(BaseModel):
    """Schema for preference response"""
    id: int
    key: str
    value: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Analytics schemas
class AnalyticsResponse(BaseModel):
    """Schema for analytics response"""
    total_tweets: int
    posted_tweets: int
    scheduled_tweets: int
    draft_tweets: int
    failed_tweets: int
    total_likes: int
    total_retweets: int
    total_replies: int
    total_impressions: int
    avg_engagement_rate: float


# Activity Log schemas
class ActivityLogResponse(BaseModel):
    """Schema for activity log response"""
    id: int
    action: str
    description: Optional[str] = None
    tweet_id: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Scheduler schemas
class ScheduledJobResponse(BaseModel):
    """Schema for scheduled job response"""
    id: str
    name: str
    next_run_time: Optional[datetime] = None
