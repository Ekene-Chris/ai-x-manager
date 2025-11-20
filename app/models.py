"""Database models for AI X Manager"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from app.database import Base


class TweetStatus(str, Enum):
    """Tweet status enum"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"
    APPROVED = "approved"
    REJECTED = "rejected"


class TweetSource(str, Enum):
    """Tweet source enum"""
    AI_GENERATED = "ai_generated"
    MANUAL = "manual"


class Tweet(Base):
    """Tweet model for storing tweets"""
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    status = Column(SQLEnum(TweetStatus), default=TweetStatus.DRAFT, nullable=False)
    source = Column(SQLEnum(TweetSource), default=TweetSource.MANUAL, nullable=False)

    # Scheduling
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    posted_time = Column(DateTime(timezone=True), nullable=True)

    # Twitter metadata
    twitter_id = Column(String(100), nullable=True, unique=True)
    twitter_url = Column(String(500), nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # AI generation metadata
    ai_prompt = Column(Text, nullable=True)
    ai_model = Column(String(100), nullable=True)

    # Engagement metrics (updated after posting)
    likes_count = Column(Integer, default=0)
    retweets_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    impressions_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<Tweet(id={self.id}, status={self.status}, content='{self.content[:50]}...')>"


class UserPreference(Base):
    """User preferences for AI generation"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<UserPreference(key={self.key}, value={self.value})>"


class ActivityLog(Base):
    """Activity log for tracking system actions"""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    tweet_id = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, action={self.action}, success={self.success})>"


class CommentRule(Base):
    """Rules for auto-responding to comments"""
    __tablename__ = "comment_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Trigger conditions
    keywords = Column(Text, nullable=True)  # JSON array of keywords
    trigger_type = Column(String(50), nullable=False)  # contains, starts_with, regex, etc.

    # Response settings
    response_template = Column(Text, nullable=True)
    use_ai_response = Column(Boolean, default=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<CommentRule(id={self.id}, name={self.name}, is_active={self.is_active})>"


class TwitterAuth(Base):
    """Twitter OAuth authentication tokens"""
    __tablename__ = "twitter_auth"

    id = Column(Integer, primary_key=True, index=True)

    # OAuth tokens
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Twitter user info
    twitter_user_id = Column(String(100), nullable=True)
    twitter_username = Column(String(100), nullable=True)
    twitter_name = Column(String(200), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TwitterAuth(username=@{self.twitter_username}, is_active={self.is_active})>"
