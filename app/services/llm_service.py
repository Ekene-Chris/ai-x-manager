"""LLM service for AI content generation using Azure OpenAI"""

from openai import AzureOpenAI
from typing import Optional, List, Dict, Any
import logging
import json
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for AI content generation using Azure OpenAI"""

    def __init__(self):
        """Initialize Azure OpenAI client"""
        try:
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )
            self.deployment_name = settings.azure_openai_deployment_name
            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
            raise

    def generate_tweet(
        self,
        topic: Optional[str] = None,
        style: str = "professional",
        tone: str = "engaging",
        max_length: int = 280,
        context: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a tweet using AI

        Args:
            topic: Topic or theme for the tweet
            style: Writing style (professional, casual, humorous, etc.)
            tone: Tone of the tweet (engaging, informative, inspirational, etc.)
            max_length: Maximum character length (default 280)
            context: Additional context or guidelines

        Returns:
            Generated tweet text or None if generation fails
        """
        try:
            # Build the prompt
            system_prompt = self._build_system_prompt(style, tone, max_length)
            user_prompt = self._build_user_prompt(topic, context)

            # Generate tweet
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=150,
                temperature=0.8,
                top_p=0.9,
            )

            tweet_text = response.choices[0].message.content.strip()

            # Remove quotes if AI wrapped the tweet in quotes
            if tweet_text.startswith('"') and tweet_text.endswith('"'):
                tweet_text = tweet_text[1:-1]
            if tweet_text.startswith("'") and tweet_text.endswith("'"):
                tweet_text = tweet_text[1:-1]

            # Ensure tweet is within character limit
            if len(tweet_text) > max_length:
                logger.warning(f"Generated tweet exceeds {max_length} characters, truncating")
                tweet_text = tweet_text[: max_length - 3] + "..."

            logger.info(f"Tweet generated successfully: {len(tweet_text)} characters")
            return tweet_text

        except Exception as e:
            logger.error(f"Error generating tweet: {str(e)}")
            return None

    def generate_reply(
        self,
        original_tweet: str,
        reply_type: str = "friendly",
        context: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a reply to a tweet

        Args:
            original_tweet: The tweet to reply to
            reply_type: Type of reply (friendly, professional, helpful, etc.)
            context: Additional context about the conversation

        Returns:
            Generated reply text or None if generation fails
        """
        try:
            system_prompt = f"""You are a helpful social media assistant. Generate a {reply_type} reply to tweets.
Reply should be:
- Maximum 280 characters
- Relevant to the original tweet
- Natural and conversational
- Professional and respectful

Only return the reply text, nothing else."""

            user_prompt = f"Generate a reply to this tweet: {original_tweet}"
            if context:
                user_prompt += f"\n\nAdditional context: {context}"

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=100,
                temperature=0.7,
            )

            reply_text = response.choices[0].message.content.strip()

            # Clean up reply
            if reply_text.startswith('"') and reply_text.endswith('"'):
                reply_text = reply_text[1:-1]

            if len(reply_text) > 280:
                reply_text = reply_text[:277] + "..."

            logger.info(f"Reply generated successfully: {len(reply_text)} characters")
            return reply_text

        except Exception as e:
            logger.error(f"Error generating reply: {str(e)}")
            return None

    def generate_multiple_tweets(
        self,
        count: int = 5,
        topics: Optional[List[str]] = None,
        style: str = "professional",
        tone: str = "engaging",
    ) -> List[str]:
        """
        Generate multiple tweet drafts

        Args:
            count: Number of tweets to generate
            topics: List of topics (if None, will generate diverse topics)
            style: Writing style
            tone: Tone of tweets

        Returns:
            List of generated tweets
        """
        tweets = []
        topics_to_use = topics if topics else [None] * count

        for topic in topics_to_use[:count]:
            tweet = self.generate_tweet(topic=topic, style=style, tone=tone)
            if tweet:
                tweets.append(tweet)

        logger.info(f"Generated {len(tweets)} tweets")
        return tweets

    def improve_tweet(self, original_tweet: str, improvement_type: str = "engagement") -> Optional[str]:
        """
        Improve an existing tweet

        Args:
            original_tweet: The tweet to improve
            improvement_type: Type of improvement (engagement, clarity, professionalism, etc.)

        Returns:
            Improved tweet text or None if improvement fails
        """
        try:
            improvement_prompts = {
                "engagement": "Make this tweet more engaging and likely to get interactions",
                "clarity": "Make this tweet clearer and easier to understand",
                "professionalism": "Make this tweet more professional and polished",
                "brevity": "Make this tweet more concise while keeping the key message",
            }

            instruction = improvement_prompts.get(improvement_type, improvement_prompts["engagement"])

            system_prompt = f"""You are a social media content editor. {instruction}.
Requirements:
- Maximum 280 characters
- Maintain the original message and intent
- Only return the improved tweet text, nothing else."""

            user_prompt = f"Improve this tweet: {original_tweet}"

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=150,
                temperature=0.7,
            )

            improved_text = response.choices[0].message.content.strip()

            # Clean up
            if improved_text.startswith('"') and improved_text.endswith('"'):
                improved_text = improved_text[1:-1]

            if len(improved_text) > 280:
                improved_text = improved_text[:277] + "..."

            logger.info(f"Tweet improved successfully")
            return improved_text

        except Exception as e:
            logger.error(f"Error improving tweet: {str(e)}")
            return None

    def _build_system_prompt(self, style: str, tone: str, max_length: int) -> str:
        """Build system prompt for tweet generation"""
        return f"""You are a professional social media content creator specializing in X (Twitter).
Generate engaging tweets with the following characteristics:
- Style: {style}
- Tone: {tone}
- Maximum length: {max_length} characters
- Use relevant emojis sparingly and naturally
- Include appropriate hashtags when relevant (1-2 max)
- Make tweets engaging and shareable
- Be authentic and conversational

IMPORTANT: Only return the tweet text itself, nothing else. No quotes, no explanations."""

    def _build_user_prompt(self, topic: Optional[str], context: Optional[str]) -> str:
        """Build user prompt for tweet generation"""
        if topic and context:
            return f"Generate a tweet about: {topic}\n\nAdditional context: {context}"
        elif topic:
            return f"Generate a tweet about: {topic}"
        elif context:
            return f"Generate a tweet with this context: {context}"
        else:
            return "Generate an interesting and engaging tweet about a trending tech or business topic."

    def check_content_quality(self, text: str) -> Dict[str, Any]:
        """
        Check content quality and provide feedback

        Args:
            text: Text to check

        Returns:
            Dictionary with quality metrics and suggestions
        """
        try:
            system_prompt = """You are a social media content quality checker.
Analyze the tweet and provide feedback in JSON format with:
- score: Overall quality score (0-10)
- clarity: Clarity score (0-10)
- engagement_potential: Engagement potential score (0-10)
- issues: List of any issues found
- suggestions: List of improvement suggestions

Only return valid JSON, nothing else."""

            user_prompt = f"Analyze this tweet: {text}"

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=300,
                temperature=0.3,
            )

            result = response.choices[0].message.content.strip()

            # Parse JSON response
            quality_data = json.loads(result)
            logger.info(f"Content quality checked: score {quality_data.get('score', 0)}/10")
            return quality_data

        except json.JSONDecodeError:
            logger.error("Failed to parse quality check response as JSON")
            return {
                "score": 5,
                "clarity": 5,
                "engagement_potential": 5,
                "issues": ["Unable to analyze"],
                "suggestions": ["Manual review recommended"],
            }
        except Exception as e:
            logger.error(f"Error checking content quality: {str(e)}")
            return {
                "score": 0,
                "clarity": 0,
                "engagement_potential": 0,
                "issues": [f"Error: {str(e)}"],
                "suggestions": [],
            }
