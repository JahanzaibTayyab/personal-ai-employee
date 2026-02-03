"""LinkedIn engagement watcher - monitor engagement for sales leads.

Uses LinkedIn API to poll for new engagement on posts.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.models.linkedin_post import (
    EngagementType,
    LinkedInEngagement,
    DEFAULT_FOLLOWUP_KEYWORDS,
)
from ai_employee.services.linkedin import LinkedInService, detect_engagement_keywords
from ai_employee.utils.jsonl_logger import JsonlLogger


class LinkedInWatcherStatus(str, Enum):
    """Status of LinkedIn engagement watcher."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class LinkedInEngagementWatcher:
    """Watcher for LinkedIn engagement monitoring.

    Polls LinkedIn API for new engagement on posts and creates
    action items for high-priority interactions.
    """

    # Heartbeat interval in seconds (SC-007)
    HEARTBEAT_INTERVAL = 60

    def __init__(self, vault_config: VaultConfig):
        """Initialize the LinkedIn engagement watcher.

        Args:
            vault_config: Vault configuration with paths
        """
        self._config = vault_config
        self._linkedin_service = LinkedInService(vault_config)
        self._status = LinkedInWatcherStatus.DISCONNECTED
        self._last_heartbeat: datetime | None = None
        self._running = False
        self._logger = JsonlLogger[dict](
            logs_dir=vault_config.logs,
            prefix="watcher",
            serializer=lambda e: str(e),
            deserializer=lambda s: {},
        )

    @property
    def status(self) -> LinkedInWatcherStatus:
        """Get current watcher status."""
        return self._status

    def _log_event(
        self,
        event_type: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log a watcher event."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "source_type": "linkedin",
            "event_type": event_type,
            "status": self._status.value,
            **(details or {}),
        }
        self._logger.log(entry)

    def _log_heartbeat(self) -> None:
        """Log heartbeat for uptime tracking."""
        self._last_heartbeat = datetime.now()
        self._log_event("heartbeat")

    def start(self) -> bool:
        """Start the engagement watcher.

        Returns:
            True if started successfully
        """
        self._status = LinkedInWatcherStatus.CONNECTING
        self._log_event("start_attempt")

        # Try to authenticate
        if self._linkedin_service.authenticate():
            self._status = LinkedInWatcherStatus.CONNECTED
            self._running = True
            self._log_event("started")
            return True

        self._status = LinkedInWatcherStatus.ERROR
        self._log_event("start_failed", {"reason": "authentication_failed"})
        return False

    def stop(self) -> None:
        """Stop the engagement watcher."""
        self._running = False
        self._status = LinkedInWatcherStatus.DISCONNECTED
        self._log_event("stopped")

    def process_engagement(
        self,
        raw_data: dict[str, Any],
    ) -> LinkedInEngagement | None:
        """Process raw engagement data from LinkedIn API.

        Args:
            raw_data: Raw engagement data from API

        Returns:
            LinkedInEngagement if valid, None if should be ignored
        """
        try:
            # Parse engagement type
            eng_type_str = raw_data.get("type", "").lower()
            type_map = {
                "like": EngagementType.LIKE,
                "comment": EngagementType.COMMENT,
                "share": EngagementType.SHARE,
                "mention": EngagementType.MENTION,
            }
            eng_type = type_map.get(eng_type_str, EngagementType.LIKE)

            # Get content (for comments)
            content = raw_data.get("content", "")

            # Detect followup keywords
            followup_keywords = detect_engagement_keywords(content) if content else []
            requires_followup = len(followup_keywords) > 0

            # Parse timestamp
            timestamp_str = raw_data.get("timestamp")
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str)
            else:
                timestamp = datetime.now()

            engagement = LinkedInEngagement(
                id=raw_data.get("id", f"eng_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                post_id=raw_data.get("post_id", ""),
                engagement_type=eng_type,
                author=raw_data.get("author", "Unknown"),
                content=content,
                timestamp=timestamp,
                requires_followup=requires_followup,
                followup_keywords=followup_keywords,
            )

            # Track the engagement
            self._linkedin_service.track_engagement(engagement)

            self._log_event("engagement_processed", {
                "engagement_id": engagement.id,
                "type": eng_type.value,
                "requires_followup": requires_followup,
            })

            return engagement

        except Exception as e:
            self._log_event("engagement_error", {"error": str(e)})
            return None

    def poll_engagement(self) -> list[LinkedInEngagement]:
        """Poll LinkedIn API for new engagement.

        Returns:
            List of new engagements found
        """
        if not self._running:
            return []

        # Log heartbeat
        self._log_heartbeat()

        # TODO: Implement actual API polling
        # For now, return empty list
        return []
