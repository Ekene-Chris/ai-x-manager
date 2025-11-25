#!/usr/bin/env python3
"""Test API credentials before running the application"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.twitter_service import TwitterService
from app.services.llm_service import LLMService
from app.config import settings

def test_twitter():
    """Test Twitter API credentials"""
    print("\n🐦 Testing Twitter API credentials...")
    try:
        service = TwitterService()
        if service.verify_credentials():
            print("✓ Twitter API credentials are valid!")
            return True
        else:
            print("✗ Twitter API credentials verification failed")
            return False
    except Exception as e:
        print(f"✗ Twitter API error: {e}")
        return False

def test_azure_openai():
    """Test Azure OpenAI credentials"""
    print("\n🤖 Testing Azure OpenAI credentials...")
    try:
        service = LLMService()
        # Try a simple generation
        test_tweet = service.generate_tweet(
            topic="test",
            style="professional",
            tone="engaging",
            max_length=50
        )
        if test_tweet:
            print("✓ Azure OpenAI credentials are valid!")
            print(f"  Sample generation: {test_tweet[:50]}...")
            return True
        else:
            print("✗ Azure OpenAI generation failed")
            return False
    except Exception as e:
        print(f"✗ Azure OpenAI error: {e}")
        return False

def main():
    """Test all credentials"""
    print("=" * 50)
    print("AI X Account Manager - Credential Test")
    print("=" * 50)

    print(f"\nEnvironment: {settings.environment}")
    print(f"Database: {settings.database_url}")

    twitter_ok = test_twitter()
    azure_ok = test_azure_openai()

    print("\n" + "=" * 50)
    if twitter_ok and azure_ok:
        print("✓ All credentials are valid!")
        print("=" * 50)
        return 0
    else:
        print("✗ Some credentials are invalid. Please check your .env file")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(main())
