"""Twitter/X service - API v2 integration via tweepy.

Supports tweet scheduling, threads, media attachments,
mention monitoring, and engagement tracking.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.models.enums import PostStatus
from ai_employee.models.tweet import Tweet, TweetEngagement
from ai_employee.utils.frontmatter import (
    generate_frontmatter,
    parse_frontmatter,
)
from ai_employee.utils.jsonl_logger import JsonlLogger

logger = logging.getLogger(__name__)

# Default keywords for mention monitoring
DEFAULT_MENTION_KEYWORDS = [
    "pricing",
    "demo",
    "inquiry",
    "interested",
    "contact",
    "quote",
    "proposal",
    "meeting",
    "help",
    "support",
]


class TwitterServiceError(Exception):
    """Base exception for Twitter service errors."""


class TwitterRateLimitError(TwitterServiceError):
    """Rate limit exceeded error."""


class TwitterAPIError(TwitterServiceError):
    """Twitter API error."""


class TwitterAuthError(TwitterServiceError):
    """Authentication error."""


class TwitterService:
    """Service for Twitter/X post management via API v2.

    Features (FR-030 to FR-034):
    - Twitter API v2 via tweepy
    - Tweet scheduling, threads, media attachments
    - Monitor mentions, replies, DMs for keywords
    - Rate limit handling
    - Storage in /Social/Twitter/
    """

    def __init__(self, vault_config: VaultConfig) -> None:
        """Initialize the Twitter service.

        Args:
            vault_config: Vault configuration with paths
        """
        self._config = vault_config
        self._connected = False
        self._client: Any = None
        self._logger = JsonlLogger[dict](
            logs_dir=vault_config.logs,
            prefix="twitter",
            serializer=lambda e: str(e),
            deserializer=lambda s: {},
        )

    def _tweets_dir(self) -> Path:
        """Get the Twitter tweets directory."""
        path = self._config.root / "Social" / "Twitter" / "tweets"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _log_operation(
        self,
        operation: str,
        success: bool,
        details: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Log a Twitter operation."""
        entry: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "success": success,
        }
        if details:
            entry.update(details)
        if error:
            entry["error"] = error
        self._logger.log(entry)

    def _create_client(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str,
        bearer_token: str,
    ) -> Any:
        """Create the Tweepy client.

        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: User access token
            access_secret: User access secret
            bearer_token: Bearer token for app-only auth

        Returns:
            tweepy.Client instance
        """
        import tweepy

        return tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
            bearer_token=bearer_token,
        )

    def connect(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str,
        bearer_token: str,
    ) -> bool:
        """Connect to Twitter API v2.

        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: User access token
            access_secret: User access secret
            bearer_token: Bearer token

        Returns:
            True if connection successful
        """
        if not all([
            api_key, api_secret, access_token, access_secret, bearer_token
        ]):
            self._log_operation(
                "connect", False, error="Missing required parameters"
            )
            return False

        try:
            self._client = self._create_client(
                api_key=api_key,
                api_secret=api_secret,
                access_token=access_token,
                access_secret=access_secret,
                bearer_token=bearer_token,
            )
            self._connected = True
            self._log_operation("connect", True)
            return True
        except Exception as e:
            self._connected = False
            self._log_operation("connect", False, error=str(e))
            return False

    def is_connected(self) -> bool:
        """Check if service is connected to Twitter API."""
        return self._connected

    def create_tweet(
        self,
        content: str,
        media_ids: list[str] | None = None,
        thread_parent_id: str | None = None,
        scheduled_time: datetime | None = None,
        correlation_id: str | None = None,
    ) -> Tweet:
        """Create a new tweet and save to vault.

        Args:
            content: Tweet text (max 280 characters)
            media_ids: Optional list of media IDs
            thread_parent_id: Optional parent tweet ID for reply
            scheduled_time: Optional scheduled time
            correlation_id: Optional correlation ID

        Returns:
            Created Tweet
        """
        is_thread = thread_parent_id is not None

        tweet = Tweet.create(
            content=content,
            media_ids=media_ids,
            thread_parent_id=thread_parent_id,
            scheduled_time=scheduled_time,
            correlation_id=correlation_id,
        )

        self._save_tweet(tweet)
        self._log_operation("create_tweet", True, {
            "tweet_id": tweet.id,
            "is_thread": is_thread,
        })

        return tweet

    def publish_tweet(self, tweet_id: str) -> Tweet:
        """Publish a tweet to Twitter.

        Args:
            tweet_id: ID of the tweet to publish

        Returns:
            Updated Tweet with twitter_id and posted_time

        Raises:
            TwitterServiceError: If not connected or tweet not found
            TwitterAPIError: If API call fails
        """
        if not self._connected:
            raise TwitterServiceError("Not connected to Twitter API")

        tweet = self.get_tweet(tweet_id)
        if tweet is None:
            raise TwitterServiceError(f"Tweet not found: {tweet_id}")

        try:
            kwargs: dict[str, Any] = {"text": tweet.content}

            if tweet.media_ids:
                kwargs["media_ids"] = tweet.media_ids

            if tweet.thread_parent_id:
                # Look up the parent tweet's twitter_id for reply
                parent = self.get_tweet(tweet.thread_parent_id)
                if parent and parent.twitter_id:
                    kwargs["in_reply_to_tweet_id"] = parent.twitter_id

            response = self._client.create_tweet(**kwargs)
            twitter_id = response.data.get("id", "")

            published = Tweet(
                id=tweet.id,
                content=tweet.content,
                twitter_id=twitter_id,
                media_ids=tweet.media_ids,
                thread_parent_id=tweet.thread_parent_id,
                thread_position=tweet.thread_position,
                scheduled_time=tweet.scheduled_time,
                posted_time=datetime.now(),
                status=PostStatus.POSTED,
                approval_id=tweet.approval_id,
                engagement=tweet.engagement,
                is_thread=tweet.is_thread,
                error_message=None,
                created_at=tweet.created_at,
                correlation_id=tweet.correlation_id,
            )

            self._save_tweet(published)
            self._log_operation("publish", True, {
                "tweet_id": tweet_id,
                "twitter_id": twitter_id,
            })

            return published

        except TwitterServiceError:
            raise
        except Exception as e:
            self._log_operation("publish", False, error=str(e))
            raise TwitterAPIError(
                f"Failed to publish tweet: {e}"
            ) from e

    def create_thread(self, tweets: list[str]) -> list[Tweet]:
        """Create a thread of tweets.

        Args:
            tweets: List of tweet contents for the thread

        Returns:
            List of created Tweet objects

        Raises:
            ValueError: If tweets list is empty
        """
        if not tweets:
            raise ValueError("Thread must contain at least one tweet")

        thread_tweets: list[Tweet] = []

        for i, content in enumerate(tweets):
            parent_id = thread_tweets[0].id if i > 0 else None
            tweet = Tweet.create(
                content=content,
                thread_parent_id=parent_id,
                thread_position=i + 1,
            )
            # First tweet in thread should also be marked as thread
            if i == 0:
                tweet = Tweet(
                    id=tweet.id,
                    content=tweet.content,
                    thread_position=1,
                    is_thread=True,
                    status=tweet.status,
                    created_at=tweet.created_at,
                )

            self._save_tweet(tweet)
            thread_tweets.append(tweet)

        self._log_operation("create_thread", True, {
            "thread_length": len(thread_tweets),
        })

        return thread_tweets

    def get_tweet(self, tweet_id: str) -> Tweet | None:
        """Get a tweet by ID from vault storage.

        Args:
            tweet_id: Tweet ID to retrieve

        Returns:
            Tweet if found, None otherwise
        """
        tweets_dir = self._tweets_dir()
        for file_path in tweets_dir.glob("*.md"):
            content = file_path.read_text()
            frontmatter, body = parse_frontmatter(content)
            if frontmatter.get("id") == tweet_id:
                return Tweet.from_frontmatter(frontmatter, body)
        return None

    def get_engagement(self, twitter_id: str) -> TweetEngagement:
        """Get engagement metrics for a tweet.

        Args:
            twitter_id: The tweet ID from Twitter

        Returns:
            TweetEngagement with current metrics

        Raises:
            TwitterServiceError: If not connected
        """
        if not self._connected:
            raise TwitterServiceError(
                "Not connected to Twitter API"
            )

        response = self._client.get_tweet(
            twitter_id,
            tweet_fields=["public_metrics"],
        )

        metrics = response.data.get("public_metrics", {})

        return TweetEngagement(
            likes=metrics.get("like_count", 0),
            retweets=metrics.get("retweet_count", 0),
            replies=metrics.get("reply_count", 0),
            quote_tweets=metrics.get("quote_count"),
            impressions=metrics.get("impression_count"),
            last_updated=datetime.now(),
        )

    def get_mentions(
        self,
        since_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get recent mentions of the authenticated user.

        Args:
            since_id: Only return mentions after this tweet ID

        Returns:
            List of mention dicts with id, text, author_id, created_at

        Raises:
            TwitterServiceError: If not connected
        """
        if not self._connected:
            raise TwitterServiceError(
                "Not connected to Twitter API"
            )

        me = self._client.get_me()
        user_id = me.data.id

        kwargs: dict[str, Any] = {}
        if since_id:
            kwargs["since_id"] = since_id

        response = self._client.get_users_mentions(user_id, **kwargs)
        mentions_data = response.data or []

        mentions: list[dict[str, Any]] = []
        for mention in mentions_data:
            mentions.append({
                "id": mention.id,
                "text": mention.text,
                "author_id": mention.author_id,
                "created_at": mention.created_at,
            })

        self._log_operation("get_mentions", True, {
            "count": len(mentions),
        })

        return mentions

    def _save_tweet(self, tweet: Tweet) -> None:
        """Save a tweet to vault as markdown with frontmatter."""
        tweets_dir = self._tweets_dir()
        file_path = tweets_dir / tweet.get_filename()
        content = generate_frontmatter(
            tweet.to_frontmatter(), tweet.content
        )
        file_path.write_text(content)
