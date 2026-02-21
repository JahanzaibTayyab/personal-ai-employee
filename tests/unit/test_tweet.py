"""Unit tests for Tweet and TweetEngagement models."""

from datetime import datetime, timedelta

import pytest

from ai_employee.models.enums import PostStatus
from ai_employee.models.tweet import (
    TWEET_MAX_CHARS,
    Tweet,
    TweetEngagement,
)


class TestTweet:
    """Tests for Tweet dataclass."""

    def test_create_tweet(self) -> None:
        """Test creating a new tweet."""
        tweet = Tweet.create(content="Hello Twitter!")

        assert tweet.content == "Hello Twitter!"
        assert tweet.status == PostStatus.DRAFT
        assert tweet.id is not None
        assert tweet.twitter_id is None
        assert tweet.media_ids is None
        assert tweet.thread_parent_id is None
        assert tweet.thread_position is None
        assert tweet.scheduled_time is None
        assert tweet.posted_time is None
        assert tweet.approval_id is None
        assert tweet.engagement is None
        assert tweet.is_thread is False
        assert tweet.error_message is None
        assert tweet.correlation_id is None
        assert tweet.created_at is not None

    def test_create_scheduled_tweet(self) -> None:
        """Test creating a scheduled tweet."""
        future_time = datetime.now() + timedelta(hours=1)
        tweet = Tweet.create(
            content="Scheduled tweet",
            scheduled_time=future_time,
        )

        assert tweet.status == PostStatus.SCHEDULED
        assert tweet.scheduled_time == future_time

    def test_create_tweet_with_media(self) -> None:
        """Test creating tweet with media IDs."""
        tweet = Tweet.create(
            content="Tweet with media",
            media_ids=["media_1", "media_2"],
        )

        assert tweet.media_ids == ["media_1", "media_2"]

    def test_create_thread_tweet(self) -> None:
        """Test creating a tweet in a thread."""
        tweet = Tweet.create(
            content="Thread reply",
            thread_parent_id="parent_123",
            thread_position=2,
        )

        assert tweet.is_thread is True
        assert tweet.thread_parent_id == "parent_123"
        assert tweet.thread_position == 2

    def test_content_length_validation(self) -> None:
        """Test tweet content length limit (280 chars)."""
        long_content = "x" * (TWEET_MAX_CHARS + 1)
        with pytest.raises(ValueError, match="exceeds.*character limit"):
            Tweet.create(content=long_content)

    def test_content_exactly_at_limit(self) -> None:
        """Test tweet at exactly 280 characters."""
        content = "x" * TWEET_MAX_CHARS
        tweet = Tweet.create(content=content)
        assert len(tweet.content) == TWEET_MAX_CHARS

    def test_to_frontmatter(self) -> None:
        """Test conversion to frontmatter dictionary."""
        tweet = Tweet.create(content="Test tweet")

        fm = tweet.to_frontmatter()

        assert fm["status"] == "draft"
        assert "id" in fm
        assert "created_at" in fm
        assert fm["is_thread"] is False

    def test_to_frontmatter_with_engagement(self) -> None:
        """Test frontmatter with engagement data."""
        engagement = TweetEngagement(
            likes=50,
            retweets=10,
            replies=5,
            quote_tweets=3,
            impressions=1000,
        )
        tweet = Tweet.create(content="Test")
        tweet_with_eng = Tweet(
            id=tweet.id,
            content=tweet.content,
            status=tweet.status,
            engagement=engagement,
            created_at=tweet.created_at,
        )

        fm = tweet_with_eng.to_frontmatter()
        assert fm["engagement"]["likes"] == 50
        assert fm["engagement"]["retweets"] == 10

    def test_from_frontmatter(self) -> None:
        """Test creation from frontmatter dictionary."""
        fm = {
            "id": "tweet_test_123",
            "status": "posted",
            "created_at": "2026-02-10T10:00:00",
            "posted_time": "2026-02-10T10:05:00",
            "twitter_id": "tw_1234567890",
            "is_thread": False,
            "engagement": {
                "likes": 20,
                "retweets": 5,
                "replies": 3,
                "quote_tweets": 1,
                "impressions": 500,
                "last_updated": "2026-02-10T11:00:00",
            },
        }

        tweet = Tweet.from_frontmatter(fm, content="Restored tweet")

        assert tweet.id == "tweet_test_123"
        assert tweet.content == "Restored tweet"
        assert tweet.status == PostStatus.POSTED
        assert tweet.twitter_id == "tw_1234567890"
        assert tweet.engagement is not None
        assert tweet.engagement.likes == 20

    def test_from_frontmatter_minimal(self) -> None:
        """Test creation from minimal frontmatter."""
        fm = {
            "id": "tweet_min",
            "status": "draft",
            "created_at": "2026-02-10T10:00:00",
            "is_thread": False,
        }

        tweet = Tweet.from_frontmatter(fm, content="Minimal")
        assert tweet.id == "tweet_min"
        assert tweet.engagement is None

    def test_get_filename(self) -> None:
        """Test filename generation."""
        tweet = Tweet.create(content="Test")

        filename = tweet.get_filename()
        assert filename.startswith("TWEET_")
        assert filename.endswith(".md")
        assert tweet.id in filename

    def test_post_init_validation(self) -> None:
        """Test __post_init__ validates content length."""
        with pytest.raises(ValueError, match="exceeds.*character limit"):
            Tweet(
                id="test",
                content="x" * (TWEET_MAX_CHARS + 1),
                created_at=datetime.now(),
            )


class TestTweetEngagement:
    """Tests for TweetEngagement dataclass."""

    def test_create_engagement(self) -> None:
        """Test creating a tweet engagement record."""
        engagement = TweetEngagement(
            likes=10,
            retweets=5,
            replies=2,
        )

        assert engagement.likes == 10
        assert engagement.retweets == 5
        assert engagement.replies == 2
        assert engagement.quote_tweets is None
        assert engagement.impressions is None
        assert engagement.last_updated is not None

    def test_create_full_engagement(self) -> None:
        """Test engagement with all fields."""
        engagement = TweetEngagement(
            likes=100,
            retweets=50,
            replies=25,
            quote_tweets=10,
            impressions=5000,
        )

        assert engagement.quote_tweets == 10
        assert engagement.impressions == 5000

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        engagement = TweetEngagement(
            likes=10,
            retweets=5,
            replies=2,
            quote_tweets=1,
            impressions=100,
        )

        d = engagement.to_dict()

        assert d["likes"] == 10
        assert d["retweets"] == 5
        assert d["replies"] == 2
        assert d["quote_tweets"] == 1
        assert d["impressions"] == 100
        assert "last_updated" in d

    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "likes": 15,
            "retweets": 3,
            "replies": 1,
            "quote_tweets": 2,
            "impressions": 300,
            "last_updated": "2026-02-10T12:00:00",
        }

        engagement = TweetEngagement.from_dict(data)

        assert engagement.likes == 15
        assert engagement.quote_tweets == 2

    def test_from_dict_minimal(self) -> None:
        """Test creation from minimal dictionary."""
        data = {
            "likes": 5,
            "retweets": 1,
            "replies": 0,
            "last_updated": "2026-02-10T12:00:00",
        }

        engagement = TweetEngagement.from_dict(data)
        assert engagement.quote_tweets is None
        assert engagement.impressions is None

    def test_default_values(self) -> None:
        """Test default engagement values."""
        engagement = TweetEngagement()

        assert engagement.likes == 0
        assert engagement.retweets == 0
        assert engagement.replies == 0


class TestConstants:
    """Tests for Twitter constants."""

    def test_max_chars(self) -> None:
        """Test tweet character limit constant."""
        assert TWEET_MAX_CHARS == 280
