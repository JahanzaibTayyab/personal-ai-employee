"""Meta (Facebook/Instagram) service - Graph API integration.

Supports post scheduling, engagement monitoring, and business keyword
detection for both Facebook and Instagram via the Meta Graph API.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.models.enums import PostStatus
from ai_employee.models.meta_post import MetaEngagement, MetaPost
from ai_employee.utils.frontmatter import (
    generate_frontmatter,
    parse_frontmatter,
)
from ai_employee.utils.jsonl_logger import JsonlLogger

logger = logging.getLogger(__name__)

# Default keywords for business-relevant comment detection (FR-027)
DEFAULT_BUSINESS_KEYWORDS = [
    "pricing",
    "demo",
    "inquiry",
    "interested",
    "contact",
    "quote",
    "proposal",
    "meeting",
    "call",
    "discuss",
    "partnership",
    "collaborate",
    "buy",
    "purchase",
    "invest",
]


class MetaServiceError(Exception):
    """Base exception for Meta service errors."""


class MetaRateLimitError(MetaServiceError):
    """Rate limit exceeded error."""


class MetaAPIError(MetaServiceError):
    """Meta Graph API error."""


class MetaAuthError(MetaServiceError):
    """Authentication error."""


def detect_business_keywords(
    comments: list[dict[str, str]],
    keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Detect business-relevant keywords in comments.

    Args:
        comments: List of comment dicts with 'text' and 'author' fields
        keywords: Optional custom keyword list

    Returns:
        List of dicts with matched comments and their keywords
    """
    if not comments:
        return []

    keyword_list = keywords or DEFAULT_BUSINESS_KEYWORDS
    results: list[dict[str, Any]] = []

    for comment in comments:
        text = comment.get("text", "").lower()
        author = comment.get("author", "Unknown")
        matched = [kw for kw in keyword_list if kw.lower() in text]

        if matched:
            results.append({
                "author": author,
                "text": comment.get("text", ""),
                "keywords": matched,
            })

    return results


class MetaService:
    """Service for Meta (Facebook/Instagram) post management.

    Features (FR-023 to FR-028):
    - Meta Graph API integration via facebook-sdk
    - Post scheduling with images, videos, text
    - Engagement monitoring (likes, comments, shares, reach)
    - Business keyword detection in comments
    - Rate limiting (200 calls/user/hour)
    - Storage in /Social/Meta/
    """

    def __init__(self, vault_config: VaultConfig) -> None:
        """Initialize the Meta service.

        Args:
            vault_config: Vault configuration with paths
        """
        self._config = vault_config
        self._connected = False
        self._graph_api: Any = None
        self._page_id: str = ""
        self._ig_user_id: str | None = None
        self._logger = JsonlLogger[dict](
            logs_dir=vault_config.logs,
            prefix="meta",
            serializer=lambda e: str(e),
            deserializer=lambda s: {},
        )

    def _posts_dir(self) -> Path:
        """Get the Meta posts directory."""
        path = self._config.root / "Social" / "Meta" / "posts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _log_operation(
        self,
        operation: str,
        success: bool,
        details: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Log a Meta operation."""
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

    def _create_graph_api(
        self,
        access_token: str,
    ) -> Any:
        """Create the Graph API client.

        Args:
            access_token: Meta Graph API access token

        Returns:
            facebook.GraphAPI instance
        """
        import facebook

        return facebook.GraphAPI(access_token=access_token, version="3.1")

    def connect(
        self,
        app_id: str,
        app_secret: str,
        access_token: str,
        page_id: str,
    ) -> bool:
        """Connect to Meta Graph API.

        Args:
            app_id: Meta App ID
            app_secret: Meta App Secret
            access_token: Page access token
            page_id: Facebook Page ID

        Returns:
            True if connection successful
        """
        if not all([app_id, app_secret, access_token, page_id]):
            self._log_operation(
                "connect", False, error="Missing required parameters"
            )
            return False

        try:
            self._graph_api = self._create_graph_api(access_token)
            # Validate by fetching page info
            self._graph_api.get_object(page_id)
            self._page_id = page_id
            self._connected = True
            self._log_operation("connect", True, {"page_id": page_id})
            return True
        except Exception as e:
            self._connected = False
            self._log_operation("connect", False, error=str(e))
            return False

    def is_connected(self) -> bool:
        """Check if service is connected to Meta API."""
        return self._connected

    def create_post(
        self,
        content: str,
        platform: str = "facebook",
        media_urls: list[str] | None = None,
        media_type: str | None = None,
        scheduled_time: datetime | None = None,
        cross_post: bool = False,
        correlation_id: str | None = None,
    ) -> MetaPost:
        """Create a new post and save to vault.

        Args:
            content: Post content text
            platform: "facebook" or "instagram"
            media_urls: Optional media URLs
            media_type: Optional media type for Instagram
            scheduled_time: Optional scheduled time
            cross_post: Whether to cross-post
            correlation_id: Optional correlation ID

        Returns:
            Created MetaPost
        """
        post = MetaPost.create(
            platform=platform,
            page_id=self._page_id,
            content=content,
            media_urls=media_urls,
            media_type=media_type,
            scheduled_time=scheduled_time,
            cross_post=cross_post,
            correlation_id=correlation_id,
        )

        self._save_post(post)
        self._log_operation("create_post", True, {
            "post_id": post.id,
            "platform": platform,
        })

        return post

    def publish_post(self, post_id: str) -> MetaPost:
        """Publish a post to Meta platform.

        Args:
            post_id: ID of the post to publish

        Returns:
            Updated MetaPost with platform_id and posted_time

        Raises:
            MetaServiceError: If not connected or post not found
            MetaAPIError: If API call fails
        """
        if not self._connected:
            raise MetaServiceError("Not connected to Meta API")

        post = self.get_post(post_id)
        if post is None:
            raise MetaServiceError(f"Post not found: {post_id}")

        try:
            if post.platform == "instagram":
                platform_id = self._publish_instagram(post)
            else:
                platform_id = self._publish_facebook(post)

            published = MetaPost(
                id=post.id,
                platform=post.platform,
                page_id=post.page_id,
                content=post.content,
                media_urls=post.media_urls,
                media_type=post.media_type,
                scheduled_time=post.scheduled_time,
                posted_time=datetime.now(),
                status=PostStatus.POSTED,
                approval_id=post.approval_id,
                engagement=post.engagement,
                error_message=None,
                cross_post=post.cross_post,
                created_at=post.created_at,
                correlation_id=post.correlation_id,
                platform_id=platform_id,
            )

            self._save_post(published)
            self._log_operation("publish", True, {
                "post_id": post_id,
                "platform_id": platform_id,
            })

            return published

        except MetaServiceError:
            raise
        except Exception as e:
            self._log_operation("publish", False, error=str(e))
            raise MetaAPIError(
                f"Failed to publish post: {e}"
            ) from e

    def _publish_facebook(self, post: MetaPost) -> str:
        """Publish a Facebook post via Graph API.

        Returns:
            Platform post ID
        """
        result = self._graph_api.put_object(
            self._page_id,
            "feed",
            message=post.content,
        )
        return str(result.get("id", ""))

    def _publish_instagram(self, post: MetaPost) -> str:
        """Publish an Instagram post via Graph API.

        Instagram requires a two-step process:
        1. Create media container
        2. Publish the container

        Returns:
            Platform post ID
        """
        ig_user_id = self._ig_user_id or self._page_id

        # Step 1: Create media container
        container_params: dict[str, Any] = {
            "caption": post.content,
        }
        if post.media_urls:
            container_params["image_url"] = post.media_urls[0]

        container = self._graph_api.put_object(
            ig_user_id,
            "media",
            **container_params,
        )
        container_id = container.get("id", "")

        # Step 2: Publish the container
        result = self._graph_api.put_object(
            ig_user_id,
            "media_publish",
            creation_id=container_id,
        )
        return str(result.get("id", container_id))

    def get_post(self, post_id: str) -> MetaPost | None:
        """Get a post by ID from vault storage.

        Args:
            post_id: Post ID to retrieve

        Returns:
            MetaPost if found, None otherwise
        """
        posts_dir = self._posts_dir()
        for file_path in posts_dir.glob("*.md"):
            content = file_path.read_text()
            frontmatter, body = parse_frontmatter(content)
            if frontmatter.get("id") == post_id:
                return MetaPost.from_frontmatter(frontmatter, body)
        return None

    def get_engagement(self, platform_post_id: str) -> MetaEngagement:
        """Get engagement metrics for a platform post.

        Args:
            platform_post_id: The post ID from Facebook/Instagram

        Returns:
            MetaEngagement with current metrics

        Raises:
            MetaServiceError: If not connected
        """
        if not self._connected:
            raise MetaServiceError(
                "Not connected to Meta API"
            )

        result = self._graph_api.get_object(
            platform_post_id,
            fields=(
                "likes.summary(true),"
                "comments.summary(true),"
                "shares,"
                "insights.metric(post_impressions,post_impressions_unique)"
            ),
        )

        likes = result.get("likes", {}).get(
            "summary", {}
        ).get("total_count", 0)
        comments = result.get("comments", {}).get(
            "summary", {}
        ).get("total_count", 0)
        shares = result.get("shares", {}).get("count", 0)

        impressions = None
        reach = None
        insights_data = result.get("insights", {}).get("data", [])
        for insight in insights_data:
            name = insight.get("name", "")
            values = insight.get("values", [])
            if values:
                value = values[0].get("value", 0)
                if name == "post_impressions":
                    impressions = value
                elif name == "post_impressions_unique":
                    reach = value

        return MetaEngagement(
            likes=likes,
            comments=comments,
            shares=shares,
            reach=reach,
            impressions=impressions,
            last_updated=datetime.now(),
        )

    def list_posts(
        self,
        platform: str | None = None,
        status: PostStatus | None = None,
        limit: int | None = None,
    ) -> list[MetaPost]:
        """List posts from vault storage.

        Args:
            platform: Optional filter by platform
            status: Optional filter by status
            limit: Optional max number of posts to return

        Returns:
            List of MetaPosts matching filters
        """
        posts_dir = self._posts_dir()
        posts: list[MetaPost] = []

        for file_path in sorted(posts_dir.glob("*.md"), reverse=True):
            content = file_path.read_text()
            frontmatter, body = parse_frontmatter(content)

            if not frontmatter.get("id"):
                continue

            post = MetaPost.from_frontmatter(frontmatter, body)

            if platform and post.platform != platform:
                continue
            if status and post.status != status:
                continue

            posts.append(post)

            if limit and len(posts) >= limit:
                break

        return posts

    def detect_business_keywords(
        self,
        comments: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Detect business keywords in comments.

        Args:
            comments: List of comment dicts with 'text' and 'author'

        Returns:
            List of matched comments with keywords
        """
        return detect_business_keywords(comments)

    def _save_post(self, post: MetaPost) -> None:
        """Save a post to vault as markdown with frontmatter."""
        posts_dir = self._posts_dir()
        file_path = posts_dir / post.get_filename()
        content = generate_frontmatter(post.to_frontmatter(), post.content)
        file_path.write_text(content)
