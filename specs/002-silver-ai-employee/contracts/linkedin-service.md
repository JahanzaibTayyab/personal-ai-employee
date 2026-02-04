# LinkedIn Service Contract

**Service**: `LinkedInService`
**Module**: `src/ai_employee/services/linkedin.py`

## Overview

The LinkedIn Service manages LinkedIn post scheduling, publishing, and engagement monitoring via the official LinkedIn API. All posting requires approval workflow.

## Interface

```python
from pathlib import Path
from datetime import datetime
from ai_employee.models.linkedin_post import LinkedInPost, LinkedInPostStatus
from ai_employee.models.linkedin_engagement import LinkedInEngagement, EngagementType
from ai_employee.services.approval import ApprovalService

class LinkedInService:
    """LinkedIn posting and engagement monitoring (FR-021 to FR-025)."""

    # Rate limit per spec FR-025
    MAX_POSTS_PER_DAY = 25

    # Keywords for follow-up detection (FR-023)
    FOLLOWUP_KEYWORDS = [
        "inquiry", "interested", "pricing",
        "contact", "demo", "question"
    ]

    def __init__(
        self,
        vault_config: VaultConfig,
        approval_service: ApprovalService,
        access_token: str | None = None,
    ) -> None:
        """
        Initialize LinkedIn service.

        Args:
            vault_config: Vault configuration
            approval_service: For creating post approval requests
            access_token: OAuth2 access token (or from env)
        """

    # ─────────────────────────────────────────────────────────────
    # Authentication
    # ─────────────────────────────────────────────────────────────

    def get_authorization_url(
        self,
        redirect_uri: str,
    ) -> str:
        """
        Get OAuth2 authorization URL for user login.

        Args:
            redirect_uri: Callback URL after authorization

        Returns:
            URL to redirect user to LinkedIn login
        """

    def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> str:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect URI used in auth URL

        Returns:
            Access token for API calls
        """

    # ─────────────────────────────────────────────────────────────
    # Post Management (FR-021)
    # ─────────────────────────────────────────────────────────────

    def create_post(
        self,
        content: str,
        scheduled_at: datetime | None = None,
    ) -> LinkedInPost:
        """
        Create a LinkedIn post (draft or scheduled).

        Args:
            content: Post text content (max 3000 chars)
            scheduled_at: Optional future posting time

        Returns:
            Created LinkedInPost object

        Side Effects:
            - Creates post file in /Social/LinkedIn/posts/
            - If scheduled, creates approval request
        """

    def schedule_post(
        self,
        post: LinkedInPost,
        scheduled_at: datetime,
    ) -> None:
        """
        Schedule a post for future publishing (FR-021).

        Args:
            post: Post to schedule
            scheduled_at: When to publish

        Side Effects:
            - Updates post status to SCHEDULED
            - Creates approval request with preview
            - Registers with scheduler service
        """

    def publish_post(
        self,
        post: LinkedInPost,
    ) -> str:
        """
        Publish an approved post to LinkedIn (FR-021).

        Args:
            post: Approved post to publish

        Returns:
            LinkedIn post ID from API

        Side Effects:
            - Posts to LinkedIn via API
            - Updates post status to POSTED
            - Records posted_at timestamp
            - Logs publishing event

        Raises:
            RateLimitError: If daily limit exceeded
            LinkedInAPIError: If API call fails
        """

    def get_posts_today_count(self) -> int:
        """
        Get number of posts made today (FR-025).

        Returns:
            Count of posts with posted_at today
        """

    # ─────────────────────────────────────────────────────────────
    # Engagement Monitoring (FR-022, FR-023, FR-024)
    # ─────────────────────────────────────────────────────────────

    def fetch_engagement(
        self,
        post: LinkedInPost,
    ) -> dict:
        """
        Fetch engagement metrics for a post (FR-022).

        Args:
            post: Posted LinkedIn post

        Returns:
            {
                "likes": 42,
                "comments": 5,
                "shares": 3,
                "impressions": 1200
            }

        Side Effects:
            - Updates post.engagement dict
            - Logs to /Social/LinkedIn/engagement.md
        """

    def scan_comments(
        self,
        post: LinkedInPost,
    ) -> list[LinkedInEngagement]:
        """
        Scan post comments for business-relevant keywords (FR-023).

        Args:
            post: Post to scan

        Returns:
            List of engagements requiring follow-up

        Side Effects:
            - Creates action items for high-priority interactions (FR-024)
        """

    def create_followup_action(
        self,
        engagement: LinkedInEngagement,
    ) -> None:
        """
        Create action item for LinkedIn follow-up (FR-024).

        Args:
            engagement: Engagement requiring follow-up

        Side Effects:
            - Creates action item in /Needs_Action/
            - Includes engagement details and suggested response
        """

    # ─────────────────────────────────────────────────────────────
    # Query
    # ─────────────────────────────────────────────────────────────

    def get_scheduled_posts(self) -> list[LinkedInPost]:
        """Get all scheduled (pending) posts."""

    def get_posts_by_status(
        self,
        status: LinkedInPostStatus,
    ) -> list[LinkedInPost]:
        """Get posts filtered by status."""

    def get_engagement_summary(self) -> dict:
        """
        Get engagement summary for Dashboard.

        Returns:
            {
                "total_posts": 15,
                "total_likes": 342,
                "total_comments": 28,
                "pending_followups": 3,
                "posts_today": 2
            }
        """
```

## LinkedIn API Integration

```python
from linkedin_api_client.auth import AuthClient
from linkedin_api_client.restli import RestliClient

# OAuth2 Configuration
LINKEDIN_SCOPES = [
    "openid",
    "profile",
    "w_member_social",  # Required for posting
]

# API Endpoints
class LinkedInAPI:
    """LinkedIn REST API client wrapper."""

    def __init__(self, access_token: str) -> None:
        self.client = RestliClient(access_token)

    def create_post(self, text: str) -> str:
        """
        Create a text post.

        Returns:
            Post URN (e.g., "urn:li:share:1234567890")
        """
        result = self.client.create(
            resource_path="rest/posts",
            entity={
                "author": f"urn:li:person:{self.get_member_id()}",
                "lifecycleState": "PUBLISHED",
                "visibility": "PUBLIC",
                "commentary": text,
            }
        )
        return result.entity_id

    def get_post_stats(self, post_urn: str) -> dict:
        """Get engagement statistics for a post."""
        # Uses LinkedIn Statistics API
        ...

    def get_post_comments(self, post_urn: str) -> list[dict]:
        """Get comments on a post."""
        # Uses LinkedIn Comments API
        ...
```

## Post File Structure

```markdown
---
id: "linkedin_20260203_091500_abc123"
content: "Excited to announce our new product launch! 🚀"
status: "posted"
scheduled_at: "2026-02-03T10:00:00"
posted_at: "2026-02-03T10:00:15"
linkedin_post_id: "urn:li:share:7012345678901234567"
engagement:
  likes: 42
  comments: 5
  shares: 3
  impressions: 1200
---

## LinkedIn Post

**Status**: Posted
**Scheduled**: 2026-02-03 10:00 AM
**Posted**: 2026-02-03 10:00:15 AM

### Content

Excited to announce our new product launch! 🚀

### Engagement

| Metric | Count |
|--------|-------|
| Likes | 42 |
| Comments | 5 |
| Shares | 3 |
| Impressions | 1200 |

### Comments Requiring Follow-up

1. **John Smith** (2026-02-03 11:30): "Interested in learning more about pricing!"
   - Keywords: interested, pricing
   - Action: [Follow-up created](/Needs_Action/LINKEDIN_followup_20260203_113000.md)
```

## Engagement Log Format

```markdown
# LinkedIn Engagement Log

## 2026-02-03

### Post: linkedin_20260203_091500_abc123

| Time | Type | Author | Content | Follow-up |
|------|------|--------|---------|-----------|
| 10:15 | like | Jane Doe | - | - |
| 10:30 | like | Bob Smith | - | - |
| 11:00 | comment | Alice Johnson | "Great news!" | No |
| 11:30 | comment | John Smith | "Interested in pricing!" | Yes |
| 12:00 | share | Tech News | - | - |
```

## Error Handling

```python
class LinkedInError(Exception):
    """Base exception for LinkedIn service."""

class RateLimitError(LinkedInError):
    """Raised when daily post limit (25) exceeded."""

class LinkedInAPIError(LinkedInError):
    """Raised when LinkedIn API returns error."""

class AuthenticationError(LinkedInError):
    """Raised when OAuth token invalid or expired."""

class ContentValidationError(LinkedInError):
    """Raised when post content exceeds limits."""
```

## Events & Logging

| Event | Log Level | Details |
|-------|-----------|---------|
| Post created | INFO | post_id, scheduled_at |
| Post scheduled | INFO | post_id, scheduled_at |
| Post published | INFO | post_id, linkedin_id |
| Post failed | ERROR | post_id, error |
| Rate limit warning | WARNING | posts_today, limit |
| Engagement fetched | DEBUG | post_id, metrics |
| Follow-up created | INFO | post_id, engagement_id |
| API error | ERROR | endpoint, status_code, message |
