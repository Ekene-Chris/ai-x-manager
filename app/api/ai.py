"""AI generation API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Tweet, TweetStatus, TweetSource, ActivityLog
from app.schemas import (
    AITweetGenerateRequest,
    AITweetImproveRequest,
    AIReplyGenerateRequest,
    TweetResponse,
)
from app.services.llm_service import LLMService

router = APIRouter(prefix="/ai", tags=["ai"])

# Global LLM service instance
llm_service: LLMService = None


def set_llm_service(service: LLMService):
    """Set LLM service instance"""
    global llm_service
    llm_service = service


@router.post("/generate", response_model=List[TweetResponse])
def generate_tweets(request: AITweetGenerateRequest, db: Session = Depends(get_db)):
    """Generate tweet(s) using AI"""
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not available")

    try:
        generated_tweets = []

        for i in range(request.count):
            # Generate tweet
            tweet_text = llm_service.generate_tweet(
                topic=request.topic,
                style=request.style,
                tone=request.tone,
                context=request.context,
            )

            if tweet_text:
                # Save to database
                db_tweet = Tweet(
                    content=tweet_text,
                    status=TweetStatus.DRAFT,
                    source=TweetSource.AI_GENERATED,
                    ai_prompt=request.topic or "General topic",
                    ai_model="azure-openai",
                )
                db.add(db_tweet)
                db.flush()

                generated_tweets.append(db_tweet)

                # Log activity
                activity = ActivityLog(
                    action="ai_tweet_generated",
                    description=f"AI generated tweet with style={request.style}, tone={request.tone}",
                    tweet_id=db_tweet.id,
                    success=True,
                )
                db.add(activity)

        db.commit()

        # Refresh all tweets
        for tweet in generated_tweets:
            db.refresh(tweet)

        return generated_tweets

    except Exception as e:
        db.rollback()
        activity = ActivityLog(
            action="ai_generation_failed",
            description="Failed to generate AI tweets",
            success=False,
            error_message=str(e),
        )
        db.add(activity)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/improve", response_model=TweetResponse)
def improve_tweet(request: AITweetImproveRequest, db: Session = Depends(get_db)):
    """Improve an existing tweet using AI"""
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not available")

    # Get original tweet
    db_tweet = db.query(Tweet).filter(Tweet.id == request.tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if db_tweet.status == TweetStatus.POSTED:
        raise HTTPException(status_code=400, detail="Cannot improve posted tweets")

    try:
        # Improve tweet
        improved_text = llm_service.improve_tweet(
            db_tweet.content,
            improvement_type=request.improvement_type,
        )

        if improved_text:
            db_tweet.content = improved_text
            db_tweet.ai_prompt = f"Improved for {request.improvement_type}"

            activity = ActivityLog(
                action="tweet_improved",
                description=f"Tweet improved using AI ({request.improvement_type})",
                tweet_id=db_tweet.id,
                success=True,
            )
            db.add(activity)

            db.commit()
            db.refresh(db_tweet)

            return db_tweet
        else:
            raise HTTPException(status_code=500, detail="Failed to improve tweet")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reply")
def generate_reply(request: AIReplyGenerateRequest):
    """Generate a reply to a tweet using AI"""
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not available")

    try:
        reply = llm_service.generate_reply(
            original_tweet=request.original_tweet,
            reply_type=request.reply_type,
            context=request.context,
        )

        if reply:
            return {"reply": reply}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate reply")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-quality/{tweet_id}")
def check_tweet_quality(tweet_id: int, db: Session = Depends(get_db)):
    """Check the quality of a tweet using AI"""
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not available")

    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    try:
        quality_check = llm_service.check_content_quality(db_tweet.content)
        return quality_check

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
