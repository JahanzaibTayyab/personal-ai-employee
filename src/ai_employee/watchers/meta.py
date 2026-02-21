"""Meta engagement watcher - monitor Facebook/Instagram for business leads.

Polls the Meta Graph API for new engagement on posts and creates
action items for high-priority interactions.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.models.meta_post import MetaEngagement
from ai_employee.services.meta import MetaService, detect_business_keywords
from ai_employee.utils.jsonl_logger import JsonlLogger

logger = logging.getLogger(__name__)


class MetaWatcherStatus(str, Enum):
    """Status of Meta engagement watcher."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class MetaEngagementWatcher:
    """Watcher for Meta (Facebook/Instagram) engagement monitoring.

    Polls Meta Graph API for new engagement on posts and creates
    action items for high-priority interactions (business keywords).
    """

    HEARTBEAT_INTERVAL = 60

    def __init__(self, vault_config: VaultConfig) -> None:
        """Initialize the Meta engagement watcher.

        Args:
            vault_config: Vault configuration with paths
        """
        self._config = vault_config
        self._meta_service = MetaService(vault_config)
        self._status = MetaWatcherStatus.DISCONNECTED
        self._last_heartbeat: datetime | None = None
        self._running = False
        self._seen_comments: set[str] = set()
        self._logger = JsonlLogger[dict](
            logs_dir=vault_config.logs,
            prefix="watcher",
            serializer=lambda e: str(e),
            deserializer=lambda s: {},
        )

    @property
    def status(self) -> MetaWatcherStatus:
        """Get current watcher status."""
        return self._status

    def _log_event(
        self,
        event_type: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log a watcher event."""
        entry: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "source_type": "meta",
            "event_type": event_type,
            "status": self._status.value,
        }
        if details:
            entry.update(details)
        self._logger.log(entry)

    def _log_heartbeat(self) -> None:
        """Log heartbeat for uptime tracking."""
        self._last_heartbeat = datetime.now()
        self._log_event("heartbeat")

    def start(
        self,
        app_id: str,
        app_secret: str,
        access_token: str,
        page_id: str,
    ) -> bool:
        """Start the engagement watcher.

        Args:
            app_id: Meta App ID
            app_secret: Meta App Secret
            access_token: Page access token
            page_id: Page ID

        Returns:
            True if started successfully
        """
        self._status = MetaWatcherStatus.CONNECTING
        self._log_event("start_attempt")

        if self._meta_service.connect(
            app_id, app_secret, access_token, page_id
        ):
            self._status = MetaWatcherStatus.CONNECTED
            self._running = True
            self._log_event("started")
            return True

        self._status = MetaWatcherStatus.ERROR
        self._log_event("start_failed", {"reason": "connection_failed"})
        return False

    def stop(self) -> None:
        """Stop the engagement watcher."""
        self._running = False
        self._status = MetaWatcherStatus.DISCONNECTED
        self._log_event("stopped")

    def poll_engagement(self) -> list[dict[str, Any]]:
        """Poll for new engagement on all posted items.

        Returns:
            List of new high-priority engagements found
        """
        if not self._running:
            return []

        self._log_heartbeat()
        high_priority: list[dict[str, Any]] = []

        try:
            posts = self._meta_service.list_posts()
            for post in posts:
                if post.platform_id:
                    engagement = self._meta_service.get_engagement(
                        post.platform_id
                    )
                    # Check for business keywords in comments
                    keywords_found = self._check_comments(
                        post.platform_id
                    )
                    if keywords_found:
                        high_priority.extend(keywords_found)

        except Exception as e:
            self._log_event("poll_error", {"error": str(e)})

        return high_priority

    def _check_comments(
        self,
        platform_post_id: str,
    ) -> list[dict[str, Any]]:
        """Check comments on a post for business keywords.

        Args:
            platform_post_id: Platform post ID to check

        Returns:
            List of comments with business keywords
        """
        try:
            if not self._meta_service._graph_api:
                return []

            result = self._meta_service._graph_api.get_object(
                platform_post_id,
                fields="comments{message,from}",
            )

            comments_data = (
                result.get("comments", {}).get("data", [])
            )
            comments = [
                {
                    "text": c.get("message", ""),
                    "author": c.get("from", {}).get("name", "Unknown"),
                }
                for c in comments_data
            ]

            return detect_business_keywords(comments)

        except Exception as e:
            self._log_event("comment_check_error", {"error": str(e)})
            return []
