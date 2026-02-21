"""Tweet and TweetEngagement models for Twitter/X integration."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ai_employee.models.enums import PostStatus

# Twitter character limit
TWEET_MAX_CHARS = 280


@dataclass
class TweetEngagement:
    """Engagement metrics for a tweet.

    Tracks likes, retweets, replies, quote tweets, and impressions.
    """

    likes: int = 0
    retweets: int = 0
    replies: int = 0
    quote_tweets: int | None = None
    impressions: int | None = None
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert engagement to dictionary."""
        data: dict[str, Any] = {
            "likes": self.likes,
            "retweets": self.retweets,
            "replies": self.replies,
            "last_updated": self.last_updated.isoformat(),
        }
        if self.quote_tweets is not None:
            data["quote_tweets"] = self.quote_tweets
        if self.impressions is not None:
            data["impressions"] = self.impressions
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TweetEngagement":
        """Create TweetEngagement from dictionary."""
        return cls(
            likes=data.get("likes", 0),
            retweets=data.get("retweets", 0),
            replies=data.get("replies", 0),
            quote_tweets=data.get("quote_tweets"),
            impressions=data.get("impressions"),
            last_updated=datetime.fromisoformat(data["last_updated"]),
        )


@dataclass
class Tweet:
    """Tweet model for Twitter/X integration.

    Stored in /Social/Twitter/tweets/ as markdown with YAML frontmatter.
    Supports single tweets, threads, and media attachments.
    """

    id: str
    content: str = ""
    twitter_id: str | None = None
    media_ids: list[str] | None = None
    thread_parent_id: str | None = None
    thread_position: int | None = None
    scheduled_time: datetime | None = None
    posted_time: datetime | None = None
    status: PostStatus = PostStatus.DRAFT
    approval_id: str | None = None
    engagement: TweetEngagement | None = None
    is_thread: bool = False
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    correlation_id: str | None = None

    @classmethod
    def create(
        cls,
        content: str,
        media_ids: list[str] | None = None,
        thread_parent_id: str | None = None,
        thread_position: int | None = None,
        scheduled_time: datetime | None = None,
        correlation_id: str | None = None,
    ) -> "Tweet":
        """Create a new tweet.

        Args:
            content: Tweet text (max 280 characters)
            media_ids: Optional list of media IDs
            thread_parent_id: Optional parent tweet ID for threads
            thread_position: Optional position in thread
            scheduled_time: Optional scheduled posting time
            correlation_id: Optional correlation ID for cross-domain

        Returns:
            New Tweet instance

        Raises:
            ValueError: If content exceeds 280 characters
        """
        if len(content) > TWEET_MAX_CHARS:
            raise ValueError(
                f"Content exceeds {TWEET_MAX_CHARS} character limit"
            )

        now = datetime.now()
        unique = uuid.uuid4().hex[:8]
        tweet_id = f"tweet_{now.strftime('%Y%m%d_%H%M%S')}_{unique}"

        status = (
            PostStatus.SCHEDULED if scheduled_time else PostStatus.DRAFT
        )
        is_thread = thread_parent_id is not None or (
            thread_position is not None and thread_position > 0
        )

        return cls(
            id=tweet_id,
            content=content,
            media_ids=media_ids,
            thread_parent_id=thread_parent_id,
            thread_position=thread_position,
            scheduled_time=scheduled_time,
            status=status,
            is_thread=is_thread,
            created_at=now,
            correlation_id=correlation_id,
        )

    def to_frontmatter(self) -> dict[str, Any]:
        """Convert tweet to YAML frontmatter dictionary."""
        data: dict[str, Any] = {
            "id": self.id,
            "status": self.status.value,
            "is_thread": self.is_thread,
            "created_at": self.created_at.isoformat(),
        }

        if self.twitter_id:
            data["twitter_id"] = self.twitter_id
        if self.media_ids:
            data["media_ids"] = self.media_ids
        if self.thread_parent_id:
            data["thread_parent_id"] = self.thread_parent_id
        if self.thread_position is not None:
            data["thread_position"] = self.thread_position
        if self.scheduled_time:
            data["scheduled_time"] = self.scheduled_time.isoformat()
        if self.posted_time:
            data["posted_time"] = self.posted_time.isoformat()
        if self.approval_id:
            data["approval_id"] = self.approval_id
        if self.engagement:
            data["engagement"] = self.engagement.to_dict()
        if self.error_message:
            data["error_message"] = self.error_message
        if self.correlation_id:
            data["correlation_id"] = self.correlation_id

        return data

    @classmethod
    def from_frontmatter(
        cls,
        data: dict[str, Any],
        content: str = "",
    ) -> "Tweet":
        """Create Tweet from YAML frontmatter dictionary."""
        engagement = None
        if data.get("engagement"):
            engagement = TweetEngagement.from_dict(data["engagement"])

        return cls(
            id=data["id"],
            content=content,
            twitter_id=data.get("twitter_id"),
            media_ids=data.get("media_ids"),
            thread_parent_id=data.get("thread_parent_id"),
            thread_position=data.get("thread_position"),
            scheduled_time=(
                datetime.fromisoformat(data["scheduled_time"])
                if data.get("scheduled_time")
                else None
            ),
            posted_time=(
                datetime.fromisoformat(data["posted_time"])
                if data.get("posted_time")
                else None
            ),
            status=PostStatus(data.get("status", "draft")),
            approval_id=data.get("approval_id"),
            engagement=engagement,
            is_thread=data.get("is_thread", False),
            error_message=data.get("error_message"),
            created_at=datetime.fromisoformat(data["created_at"]),
            correlation_id=data.get("correlation_id"),
        )

    def get_filename(self) -> str:
        """Generate filename for this tweet."""
        return f"TWEET_{self.id}.md"

    def __post_init__(self) -> None:
        """Validate the tweet."""
        if len(self.content) > TWEET_MAX_CHARS:
            raise ValueError(
                f"Content exceeds {TWEET_MAX_CHARS} character limit"
            )
