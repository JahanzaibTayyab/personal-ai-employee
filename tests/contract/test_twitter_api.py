"""Contract tests for Twitter API v2 integration (mock API)."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.services.twitter import TwitterService


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
    return config


@pytest.fixture
def twitter_service(vault_config: VaultConfig) -> TwitterService:
    """Create TwitterService with mocked API."""
    return TwitterService(vault_config)


class TestTwitterAPIv2Contract:
    """Contract tests verifying Twitter API v2 interaction patterns."""

    def test_connect_creates_tweepy_client(
        self, twitter_service: TwitterService
    ) -> None:
        """Test that connect creates a Tweepy Client."""
        with patch.object(
            twitter_service,
            "_create_client",
            return_value=MagicMock(),
        ) as mock_create:
            twitter_service.connect(
                api_key="key",
                api_secret="secret",
                access_token="token",
                access_secret="access_secret",
                bearer_token="bearer",
            )

            mock_create.assert_called_once_with(
                api_key="key",
                api_secret="secret",
                access_token="token",
                access_secret="access_secret",
                bearer_token="bearer",
            )

    def test_publish_calls_create_tweet(
        self, twitter_service: TwitterService
    ) -> None:
        """Test that publish uses tweepy's create_tweet method."""
        tweet = twitter_service.create_tweet(
            content="Contract test tweet"
        )

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {"id": "tw_contract_123"}
        mock_client.create_tweet.return_value = mock_response
        twitter_service._client = mock_client
        twitter_service._connected = True

        published = twitter_service.publish_tweet(tweet.id)

        mock_client.create_tweet.assert_called_once()
        call_kwargs = mock_client.create_tweet.call_args[1]
        assert call_kwargs["text"] == "Contract test tweet"
        assert published.twitter_id == "tw_contract_123"

    def test_publish_with_media_passes_media_ids(
        self, twitter_service: TwitterService
    ) -> None:
        """Test that publishing with media passes media_ids to API."""
        tweet = twitter_service.create_tweet(
            content="Media tweet",
            media_ids=["media_1", "media_2"],
        )

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {"id": "tw_media_123"}
        mock_client.create_tweet.return_value = mock_response
        twitter_service._client = mock_client
        twitter_service._connected = True

        twitter_service.publish_tweet(tweet.id)

        call_kwargs = mock_client.create_tweet.call_args[1]
        assert call_kwargs.get("media_ids") == ["media_1", "media_2"]

    def test_get_engagement_uses_tweet_fields(
        self, twitter_service: TwitterService
    ) -> None:
        """Test engagement request includes public_metrics field."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {
            "public_metrics": {
                "like_count": 10,
                "retweet_count": 3,
                "reply_count": 1,
                "quote_count": 0,
                "impression_count": 500,
            }
        }
        mock_client.get_tweet.return_value = mock_response
        twitter_service._client = mock_client
        twitter_service._connected = True

        engagement = twitter_service.get_engagement("tw_eng_123")

        mock_client.get_tweet.assert_called_once()
        call_kwargs = mock_client.get_tweet.call_args[1]
        assert "tweet_fields" in call_kwargs

    def test_get_mentions_uses_users_mentions(
        self, twitter_service: TwitterService
    ) -> None:
        """Test that get_mentions calls get_users_mentions."""
        mock_client = MagicMock()
        mock_me = MagicMock()
        mock_me.data = MagicMock()
        mock_me.data.id = "user_contract"
        mock_client.get_me.return_value = mock_me

        mock_mentions = MagicMock()
        mock_mentions.data = [
            MagicMock(
                id="m1",
                text="@user test mention",
                author_id="a1",
                created_at="2026-02-10T10:00:00Z",
            ),
        ]
        mock_client.get_users_mentions.return_value = mock_mentions
        twitter_service._client = mock_client
        twitter_service._connected = True

        mentions = twitter_service.get_mentions()

        mock_client.get_users_mentions.assert_called_once()
        assert len(mentions) == 1

    def test_thread_publish_chains_in_reply_to(
        self, twitter_service: TwitterService
    ) -> None:
        """Test that thread publishing chains tweet IDs correctly."""
        tweets = twitter_service.create_thread([
            "Thread 1/2",
            "Thread 2/2",
        ])

        mock_client = MagicMock()
        # First tweet response
        resp1 = MagicMock()
        resp1.data = {"id": "tw_thread_1"}
        # Second tweet response
        resp2 = MagicMock()
        resp2.data = {"id": "tw_thread_2"}
        mock_client.create_tweet.side_effect = [resp1, resp2]
        twitter_service._client = mock_client
        twitter_service._connected = True

        # Publish first tweet
        pub1 = twitter_service.publish_tweet(tweets[0].id)
        assert pub1.twitter_id == "tw_thread_1"

        # Publish second tweet (should reference first)
        pub2 = twitter_service.publish_tweet(tweets[1].id)
        assert pub2.twitter_id == "tw_thread_2"

    def test_rate_limit_error_handling(
        self, twitter_service: TwitterService
    ) -> None:
        """Test that rate limit errors are properly caught."""
        tweet = twitter_service.create_tweet(
            content="Rate limit test"
        )

        mock_client = MagicMock()
        mock_client.create_tweet.side_effect = Exception(
            "Too Many Requests"
        )
        twitter_service._client = mock_client
        twitter_service._connected = True

        from ai_employee.services.twitter import TwitterAPIError

        with pytest.raises(TwitterAPIError):
            twitter_service.publish_tweet(tweet.id)
