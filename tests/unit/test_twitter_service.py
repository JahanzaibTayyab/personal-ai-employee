"""Unit tests for TwitterService (mock tweepy)."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.enums import PostStatus
from ai_employee.models.tweet import Tweet, TweetEngagement
from ai_employee.services.twitter import (
    DEFAULT_MENTION_KEYWORDS,
    TwitterAPIError,
    TwitterRateLimitError,
    TwitterService,
    TwitterServiceError,
)


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault structure."""
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create vault config with temp path."""
    config = VaultConfig(root=vault_path)
    config.ensure_structure()
    (vault_path / "Social" / "Twitter" / "tweets").mkdir(
        parents=True, exist_ok=True
    )
    (vault_path / "Needs_Action" / "Twitter").mkdir(
        parents=True, exist_ok=True
    )
    return config


@pytest.fixture
def twitter_service(vault_config: VaultConfig) -> TwitterService:
    """Create a TwitterService instance."""
    return TwitterService(vault_config)


class TestTwitterServiceConnect:
    """Tests for TwitterService.connect method."""

    def test_connect_success(self, twitter_service: TwitterService) -> None:
        """Test successful connection."""
        with patch.object(
            twitter_service,
            "_create_client",
            return_value=MagicMock(),
        ):
            result = twitter_service.connect(
                api_key="test_key",
                api_secret="test_secret",
                access_token="test_token",
                access_secret="test_access_secret",
                bearer_token="test_bearer",
            )

            assert result is True
            assert twitter_service.is_connected()

    def test_connect_failure(self, twitter_service: TwitterService) -> None:
        """Test failed connection."""
        with patch.object(
            twitter_service,
            "_create_client",
            side_effect=Exception("Auth failed"),
        ):
            result = twitter_service.connect(
                api_key="bad",
                api_secret="bad",
                access_token="bad",
                access_secret="bad",
                bearer_token="bad",
            )

            assert result is False
            assert not twitter_service.is_connected()

    def test_connect_missing_params(
        self, twitter_service: TwitterService
    ) -> None:
        """Test connection with empty parameters."""
        result = twitter_service.connect(
            api_key="",
            api_secret="",
            access_token="",
            access_secret="",
            bearer_token="",
        )

        assert result is False


class TestTwitterServiceCreateTweet:
    """Tests for TwitterService.create_tweet method."""

    def test_create_tweet(self, twitter_service: TwitterService) -> None:
        """Test creating a tweet."""
        tweet = twitter_service.create_tweet(content="Hello Twitter!")

        assert tweet.content == "Hello Twitter!"
        assert tweet.status == PostStatus.DRAFT

    def test_create_scheduled_tweet(
        self, twitter_service: TwitterService
    ) -> None:
        """Test creating a scheduled tweet."""
        future_time = datetime.now() + timedelta(hours=1)
        tweet = twitter_service.create_tweet(
            content="Scheduled tweet",
            scheduled_time=future_time,
        )

        assert tweet.status == PostStatus.SCHEDULED

    def test_create_tweet_with_media(
        self, twitter_service: TwitterService
    ) -> None:
        """Test creating tweet with media."""
        tweet = twitter_service.create_tweet(
            content="With media",
            media_ids=["media_1"],
        )

        assert tweet.media_ids == ["media_1"]

    def test_create_tweet_saves_file(
        self, twitter_service: TwitterService, vault_path: Path
    ) -> None:
        """Test that creating a tweet saves to vault."""
        twitter_service.create_tweet(content="Saved tweet")

        tweet_dir = vault_path / "Social" / "Twitter" / "tweets"
        tweet_files = list(tweet_dir.glob("*.md"))
        assert len(tweet_files) == 1

    def test_create_tweet_thread_parent(
        self, twitter_service: TwitterService
    ) -> None:
        """Test creating a reply in a thread."""
        tweet = twitter_service.create_tweet(
            content="Thread reply",
            thread_parent_id="parent_123",
        )

        assert tweet.is_thread is True
        assert tweet.thread_parent_id == "parent_123"


class TestTwitterServicePublishTweet:
    """Tests for TwitterService.publish_tweet method."""

    def test_publish_tweet_success(
        self, twitter_service: TwitterService
    ) -> None:
        """Test publishing a tweet successfully."""
        tweet = twitter_service.create_tweet(content="To publish")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {"id": "tw_123456"}
        mock_client.create_tweet.return_value = mock_response
        twitter_service._client = mock_client
        twitter_service._connected = True

        published = twitter_service.publish_tweet(tweet.id)

        assert published.status == PostStatus.POSTED
        assert published.twitter_id == "tw_123456"
        assert published.posted_time is not None

    def test_publish_tweet_not_connected(
        self, twitter_service: TwitterService
    ) -> None:
        """Test publishing when not connected."""
        tweet = twitter_service.create_tweet(content="Not connected")

        with pytest.raises(TwitterServiceError, match="Not connected"):
            twitter_service.publish_tweet(tweet.id)

    def test_publish_nonexistent_tweet(
        self, twitter_service: TwitterService
    ) -> None:
        """Test publishing a nonexistent tweet."""
        twitter_service._connected = True

        with pytest.raises(TwitterServiceError, match="not found"):
            twitter_service.publish_tweet("nonexistent_id")

    def test_publish_tweet_api_error(
        self, twitter_service: TwitterService
    ) -> None:
        """Test API error during publish."""
        tweet = twitter_service.create_tweet(content="API fail")

        mock_client = MagicMock()
        mock_client.create_tweet.side_effect = Exception("API Error")
        twitter_service._client = mock_client
        twitter_service._connected = True

        with pytest.raises(TwitterAPIError):
            twitter_service.publish_tweet(tweet.id)


class TestTwitterServiceCreateThread:
    """Tests for TwitterService.create_thread method."""

    def test_create_thread(self, twitter_service: TwitterService) -> None:
        """Test creating a tweet thread."""
        contents = [
            "Thread tweet 1/3",
            "Thread tweet 2/3",
            "Thread tweet 3/3",
        ]

        tweets = twitter_service.create_thread(contents)

        assert len(tweets) == 3
        assert tweets[0].thread_position == 1
        assert tweets[1].thread_position == 2
        assert tweets[2].thread_position == 3
        assert tweets[0].is_thread is True
        # First tweet has no parent
        assert tweets[0].thread_parent_id is None
        # Subsequent tweets reference the first tweet
        assert tweets[1].thread_parent_id == tweets[0].id
        assert tweets[2].thread_parent_id == tweets[0].id

    def test_create_empty_thread(
        self, twitter_service: TwitterService
    ) -> None:
        """Test creating an empty thread raises error."""
        with pytest.raises(ValueError, match="at least one tweet"):
            twitter_service.create_thread([])


class TestTwitterServiceGetTweet:
    """Tests for TwitterService.get_tweet method."""

    def test_get_existing_tweet(
        self, twitter_service: TwitterService
    ) -> None:
        """Test getting an existing tweet."""
        created = twitter_service.create_tweet(content="Get me")

        retrieved = twitter_service.get_tweet(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.content == "Get me"

    def test_get_nonexistent_tweet(
        self, twitter_service: TwitterService
    ) -> None:
        """Test getting a nonexistent tweet returns None."""
        result = twitter_service.get_tweet("nonexistent")
        assert result is None


class TestTwitterServiceGetEngagement:
    """Tests for TwitterService.get_engagement method."""

    def test_get_engagement_success(
        self, twitter_service: TwitterService
    ) -> None:
        """Test getting engagement data."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {
            "public_metrics": {
                "like_count": 42,
                "retweet_count": 10,
                "reply_count": 5,
                "quote_count": 3,
                "impression_count": 2000,
            }
        }
        mock_client.get_tweet.return_value = mock_response
        twitter_service._client = mock_client
        twitter_service._connected = True

        engagement = twitter_service.get_engagement("tw_123")

        assert engagement.likes == 42
        assert engagement.retweets == 10
        assert engagement.replies == 5
        assert engagement.quote_tweets == 3
        assert engagement.impressions == 2000

    def test_get_engagement_not_connected(
        self, twitter_service: TwitterService
    ) -> None:
        """Test engagement when not connected."""
        with pytest.raises(TwitterServiceError, match="Not connected"):
            twitter_service.get_engagement("some_tweet")


class TestTwitterServiceGetMentions:
    """Tests for TwitterService.get_mentions method."""

    def test_get_mentions_success(
        self, twitter_service: TwitterService
    ) -> None:
        """Test getting mentions."""
        mock_client = MagicMock()
        mock_me = MagicMock()
        mock_me.data = MagicMock()
        mock_me.data.id = "user_123"
        mock_client.get_me.return_value = mock_me

        mock_mentions = MagicMock()
        mock_mentions.data = [
            MagicMock(
                id="mention_1",
                text="@user Hello there!",
                author_id="author_1",
                created_at="2026-02-10T10:00:00Z",
            ),
            MagicMock(
                id="mention_2",
                text="@user Check pricing",
                author_id="author_2",
                created_at="2026-02-10T11:00:00Z",
            ),
        ]
        mock_client.get_users_mentions.return_value = mock_mentions
        twitter_service._client = mock_client
        twitter_service._connected = True

        mentions = twitter_service.get_mentions()

        assert len(mentions) == 2

    def test_get_mentions_not_connected(
        self, twitter_service: TwitterService
    ) -> None:
        """Test mentions when not connected."""
        with pytest.raises(TwitterServiceError, match="Not connected"):
            twitter_service.get_mentions()

    def test_get_mentions_with_since_id(
        self, twitter_service: TwitterService
    ) -> None:
        """Test getting mentions since a specific tweet ID."""
        mock_client = MagicMock()
        mock_me = MagicMock()
        mock_me.data = MagicMock()
        mock_me.data.id = "user_123"
        mock_client.get_me.return_value = mock_me

        mock_mentions = MagicMock()
        mock_mentions.data = []
        mock_client.get_users_mentions.return_value = mock_mentions
        twitter_service._client = mock_client
        twitter_service._connected = True

        mentions = twitter_service.get_mentions(since_id="tw_last")

        assert len(mentions) == 0
        mock_client.get_users_mentions.assert_called_once()
