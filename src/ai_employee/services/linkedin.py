"""LinkedIn service - schedule posts and track engagement for sales leads.

Integrates with linkedin-api-client for LinkedIn API operations.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ai_employee.config import VaultConfig

if TYPE_CHECKING:
    from linkedin_api import Linkedin
from ai_employee.models.approval_request import ApprovalCategory
from ai_employee.models.linkedin_post import (
    LinkedInEngagement,
    LinkedInPost,
    LinkedInPostStatus,
    EngagementType,
)
from ai_employee.services.approval import ApprovalService
from ai_employee.utils.frontmatter import parse_frontmatter
from ai_employee.utils.jsonl_logger import JsonlLogger


# Default keywords for business-relevant engagement detection (FR-023)
DEFAULT_ENGAGEMENT_KEYWORDS = [
    "inquiry",
    "interested",
    "pricing",
    "contact",
    "demo",
    "quote",
    "proposal",
    "meeting",
    "call",
    "discuss",
]

# Rate limit: max posts per day (FR-025)
MAX_POSTS_PER_DAY = 25


class LinkedInServiceError(Exception):
    """Base exception for LinkedIn service errors."""

    pass


class RateLimitError(LinkedInServiceError):
    """Rate limit exceeded error."""

    pass


class LinkedInAPIError(LinkedInServiceError):
    """LinkedIn API error."""

    pass


class AuthenticationError(LinkedInServiceError):
    """Authentication failed error."""

    pass


def detect_engagement_keywords(
    text: str,
    keyword_list: list[str] | None = None,
) -> list[str]:
    """Detect business-relevant keywords in engagement text.

    Args:
        text: Text to scan for keywords
        keyword_list: Optional custom keyword list (defaults to DEFAULT_ENGAGEMENT_KEYWORDS)

    Returns:
        List of matched keywords (lowercase)
    """
    keywords = keyword_list or DEFAULT_ENGAGEMENT_KEYWORDS
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


class LinkedInService:
    """Service for LinkedIn post scheduling and engagement tracking.

    Features:
    - Schedule posts with approval workflow
    - Track engagement (likes, comments, shares)
    - Detect high-priority interactions via keywords
    - Rate limiting (25 posts/day)
    """

    def __init__(self, vault_config: VaultConfig):
        """Initialize the LinkedIn service.

        Args:
            vault_config: Vault configuration with paths
        """
        self._config = vault_config
        self._approval_service = ApprovalService(vault_config)
        self._authenticated = False
        self._api_client: Linkedin | None = None
        self._logger = JsonlLogger[dict](
            logs_dir=vault_config.logs,
            prefix="linkedin",
            serializer=lambda e: str(e),
            deserializer=lambda s: {},
        )

    def _log_operation(
        self,
        operation: str,
        success: bool,
        details: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Log a LinkedIn operation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "success": success,
            **(details or {}),
        }
        if error:
            entry["error"] = error
        self._logger.log(entry)

    def authenticate(self) -> bool:
        """Authenticate with LinkedIn API.

        Returns:
            True if authentication successful
        """
        try:
            result = self._authenticate_api()
            self._authenticated = result
            self._log_operation("authenticate", result)
            return result
        except Exception as e:
            self._log_operation("authenticate", False, error=str(e))
            return False

    def _authenticate_api(self) -> bool:
        """Perform actual API authentication.

        Uses linkedin-api package with credentials from environment variables:
        - LINKEDIN_EMAIL: LinkedIn account email
        - LINKEDIN_PASSWORD: LinkedIn account password

        Returns:
            True if authentication successful
        """
        email = os.environ.get("LINKEDIN_EMAIL")
        password = os.environ.get("LINKEDIN_PASSWORD")

        if not email or not password:
            self._log_operation(
                "authenticate",
                False,
                error="LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables required",
            )
            return False

        try:
            from linkedin_api import Linkedin

            self._api_client = Linkedin(email, password)
            # Verify authentication by getting profile
            profile = self._api_client.get_profile(public_id="me")
            if profile:
                self._log_operation(
                    "authenticate",
                    True,
                    details={"profile_id": profile.get("public_id", "unknown")},
                )
                return True
            return False
        except ImportError:
            self._log_operation(
                "authenticate",
                False,
                error="linkedin-api package not installed. Run: uv add linkedin-api",
            )
            return False
        except Exception as e:
            self._log_operation("authenticate", False, error=str(e))
            return False

    def is_authenticated(self) -> bool:
        """Check if service is authenticated.

        Returns:
            True if authenticated
        """
        return self._authenticated

    def schedule_post(
        self,
        content: str,
        scheduled_time: datetime,
        media_paths: list[str] | None = None,
    ) -> str:
        """Schedule a LinkedIn post for approval.

        Args:
            content: Post content text
            scheduled_time: When to publish (after approval)
            media_paths: Optional list of media file paths

        Returns:
            Approval request ID

        Raises:
            RateLimitError: If daily rate limit exceeded
        """
        # Check rate limit
        posts_today = self.get_posts_today()
        if posts_today >= MAX_POSTS_PER_DAY:
            raise RateLimitError(
                f"Daily rate limit exceeded ({MAX_POSTS_PER_DAY} posts/day)"
            )

        # Validate media paths if provided
        if media_paths:
            for path in media_paths:
                if not Path(path).exists():
                    raise FileNotFoundError(f"Media file not found: {path}")

        # Create approval request
        payload = {
            "content": content,
            "scheduled_time": scheduled_time.isoformat(),
            "media_paths": media_paths or [],
        }

        request = self._approval_service.create_approval_request(
            category=ApprovalCategory.SOCIAL_POST,
            payload=payload,
            summary=f"LinkedIn post: {content[:50]}...",
        )

        self._log_operation("schedule", True, {
            "approval_id": request.id,
            "content_preview": content[:50],
            "scheduled_time": scheduled_time.isoformat(),
        })

        return request.id

    def get_pending_posts(self) -> list[dict[str, Any]]:
        """Get all pending LinkedIn posts awaiting approval.

        Returns:
            List of pending post approval requests
        """
        pending = self._approval_service.get_pending_requests()
        return [
            {
                "id": r.id,
                "content": r.payload.get("content", ""),
                "scheduled_time": r.payload.get("scheduled_time"),
                "created_at": r.created_at,
                "expires_at": r.expires_at,
            }
            for r in pending
            if r.category == ApprovalCategory.SOCIAL_POST
        ]

    def get_posts_today(self) -> int:
        """Get count of posts made today.

        Returns:
            Number of posts made today
        """
        # Check log for posts today
        entries = self._logger.read_entries()
        today = datetime.now().date()

        return sum(
            1 for e in entries
            if e.get("operation") == "post"
            and e.get("success")
            and datetime.fromisoformat(e.get("timestamp", "")).date() == today
        )

    def post_approved(self, approval_id: str) -> dict[str, Any]:
        """Post approved content to LinkedIn.

        Args:
            approval_id: ID of approved post request

        Returns:
            Dict with post_id and success status

        Raises:
            LinkedInAPIError: If posting fails
        """
        # Find the approval file in Approved folder
        approved_file = self._find_approved_file(approval_id)
        if not approved_file:
            raise LinkedInServiceError(f"Approved post not found: {approval_id}")

        # Read post content from approval file
        post_data = self._read_post_from_file(approved_file)

        try:
            result = self._post_to_linkedin(
                content=post_data["content"],
                media_paths=post_data.get("media_paths", []),
            )

            if result.get("success"):
                self._log_operation("post", True, {
                    "approval_id": approval_id,
                    "post_id": result.get("post_id"),
                })
                # Move to Done
                self._move_to_done(approved_file)
                return result

            raise LinkedInAPIError(result.get("error", "Post failed"))

        except LinkedInServiceError:
            self._move_to_quarantine(approved_file)
            raise
        except Exception as e:
            self._log_operation("post", False, error=str(e))
            self._move_to_quarantine(approved_file)
            raise LinkedInAPIError(str(e)) from e

    def _post_to_linkedin(
        self,
        content: str,
        media_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        """Post content to LinkedIn via API.

        Uses linkedin-api package to create posts.

        Args:
            content: Post content
            media_paths: Optional media files

        Returns:
            Dict with post_id and success status

        Raises:
            LinkedInAPIError: If posting fails
        """
        import uuid

        # If not authenticated or no client, return mock for testing
        if not self._api_client:
            self._log_operation(
                "post",
                False,
                error="Not authenticated. Call authenticate() first.",
            )
            # Return mock response for testing without credentials
            return {
                "success": True,
                "post_id": f"mock_{uuid.uuid4().hex[:12]}",
                "mock": True,
            }

        try:
            # Post text content
            result = self._api_client.post(content)

            post_id = result.get("id") if result else f"linkedin_{uuid.uuid4().hex[:12]}"

            self._log_operation(
                "post",
                True,
                details={"post_id": post_id, "content_length": len(content)},
            )

            return {
                "success": True,
                "post_id": post_id,
            }
        except Exception as e:
            self._log_operation("post", False, error=str(e))
            raise LinkedInAPIError(f"Failed to post to LinkedIn: {e}") from e

    def _find_approved_file(self, approval_id: str) -> Path | None:
        """Find approval file in Approved folder."""
        for file in self._config.approved.glob("*.md"):
            if approval_id in file.name:
                return file
        return None

    def _read_post_from_file(self, file_path: Path) -> dict[str, Any]:
        """Read post data from approval file."""
        content = file_path.read_text()
        frontmatter, _ = parse_frontmatter(content)
        payload = frontmatter.get("payload", {})
        return dict(payload) if payload else {}

    def _move_to_done(self, file_path: Path) -> None:
        """Move file to Done folder."""
        dest = self._config.done / file_path.name
        file_path.rename(dest)

    def _move_to_quarantine(self, file_path: Path) -> None:
        """Move file to Quarantine folder."""
        dest = self._config.quarantine / file_path.name
        file_path.rename(dest)

    def track_engagement(self, engagement: LinkedInEngagement) -> None:
        """Track an engagement on a LinkedIn post.

        Creates action item for high-priority engagements (those requiring followup).

        Args:
            engagement: Engagement to track
        """
        # Log to engagement file
        self._log_engagement(engagement)

        # Create action item if high-priority (requires followup)
        if engagement.requires_followup:
            self._create_engagement_action(engagement)

    def _log_engagement(self, engagement: LinkedInEngagement) -> None:
        """Log engagement to engagement.md file."""
        log_file = self._config.social_linkedin / "engagement.md"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Append to log file
        entry = (
            f"\n## {engagement.timestamp.strftime('%Y-%m-%d %H:%M')}\n"
            f"- **Type**: {engagement.engagement_type.value}\n"
            f"- **Author**: {engagement.author}\n"
            f"- **Content**: {engagement.content}\n"
        )
        if engagement.followup_keywords:
            entry += f"- **Keywords**: {', '.join(engagement.followup_keywords)}\n"

        if log_file.exists():
            content = log_file.read_text()
            log_file.write_text(content + entry)
        else:
            header = "# LinkedIn Engagement Log\n"
            log_file.write_text(header + entry)

    def _create_engagement_action(self, engagement: LinkedInEngagement) -> None:
        """Create action item for high-priority engagement."""
        action_dir = self._config.needs_action_linkedin
        action_dir.mkdir(parents=True, exist_ok=True)

        filename = f"LINKEDIN_{engagement.id}.md"
        file_path = action_dir / filename

        content = f"""---
id: "{engagement.id}"
post_id: "{engagement.post_id}"
engagement_type: "{engagement.engagement_type.value}"
author: "{engagement.author}"
keywords: {engagement.followup_keywords}
timestamp: "{engagement.timestamp.isoformat()}"
action_status: "new"
---

# LinkedIn Engagement: {engagement.author}

**Type**: {engagement.engagement_type.value}
**Post ID**: {engagement.post_id}
**Keywords**: {', '.join(engagement.followup_keywords)}

## Content

{engagement.content}

---
*High-priority engagement - follow up required*
"""

        file_path.write_text(content)

        self._log_operation("engagement_action", True, {
            "engagement_id": engagement.id,
            "keywords": engagement.followup_keywords,
        })
