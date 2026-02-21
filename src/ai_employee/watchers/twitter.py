"""Twitter mention watcher - monitor for business-relevant mentions.

Polls the Twitter API v2 for new mentions and creates action items
for high-priority interactions containing business keywords.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.services.twitter import (
    DEFAULT_MENTION_KEYWORDS,
    TwitterService,
)
from ai_employee.utils.jsonl_logger import JsonlLogger

logger = logging.getLogger(__name__)


class TwitterWatcherStatus(str, Enum):
    """Status of Twitter mention watcher."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class TwitterMentionWatcher:
    """Watcher for Twitter/X mention monitoring.

    Polls Twitter API v2 for new mentions and creates action items
    for high-priority interactions (business keywords in mentions).
    """

    HEARTBEAT_INTERVAL = 60

    def __init__(self, vault_config: VaultConfig) -> None:
        """Initialize the Twitter mention watcher.

        Args:
            vault_config: Vault configuration with paths
        """
        self._config = vault_config
        self._twitter_service = TwitterService(vault_config)
        self._status = TwitterWatcherStatus.DISCONNECTED
        self._last_heartbeat: datetime | None = None
        self._running = False
        self._last_mention_id: str | None = None
        self._keywords = list(DEFAULT_MENTION_KEYWORDS)
        self._logger = JsonlLogger[dict](
            logs_dir=vault_config.logs,
            prefix="watcher",
            serializer=lambda e: str(e),
            deserializer=lambda s: {},
        )

    @property
    def status(self) -> TwitterWatcherStatus:
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
            "source_type": "twitter",
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
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str,
        bearer_token: str,
    ) -> bool:
        """Start the mention watcher.

        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: User access token
            access_secret: User access secret
            bearer_token: Bearer token

        Returns:
            True if started successfully
        """
        self._status = TwitterWatcherStatus.CONNECTING
        self._log_event("start_attempt")

        if self._twitter_service.connect(
            api_key, api_secret, access_token, access_secret, bearer_token
        ):
            self._status = TwitterWatcherStatus.CONNECTED
            self._running = True
            self._log_event("started")
            return True

        self._status = TwitterWatcherStatus.ERROR
        self._log_event("start_failed", {"reason": "connection_failed"})
        return False

    def stop(self) -> None:
        """Stop the mention watcher."""
        self._running = False
        self._status = TwitterWatcherStatus.DISCONNECTED
        self._log_event("stopped")

    def poll_mentions(self) -> list[dict[str, Any]]:
        """Poll for new mentions with business keywords.

        Returns:
            List of high-priority mentions (containing keywords)
        """
        if not self._running:
            return []

        self._log_heartbeat()
        high_priority: list[dict[str, Any]] = []

        try:
            mentions = self._twitter_service.get_mentions(
                since_id=self._last_mention_id
            )

            for mention in mentions:
                mention_id = mention.get("id")
                text = mention.get("text", "").lower()

                # Update last seen mention ID
                if mention_id:
                    self._last_mention_id = str(mention_id)

                # Check for business keywords
                matched_keywords = [
                    kw for kw in self._keywords if kw.lower() in text
                ]

                if matched_keywords:
                    high_priority.append({
                        "mention_id": mention_id,
                        "text": mention.get("text", ""),
                        "author_id": mention.get("author_id"),
                        "keywords": matched_keywords,
                        "created_at": mention.get("created_at"),
                    })

                    self._create_action_item(mention, matched_keywords)

            self._log_event("poll_complete", {
                "total_mentions": len(mentions),
                "high_priority": len(high_priority),
            })

        except Exception as e:
            self._log_event("poll_error", {"error": str(e)})

        return high_priority

    def _create_action_item(
        self,
        mention: dict[str, Any],
        keywords: list[str],
    ) -> None:
        """Create an action item for a high-priority mention.

        Args:
            mention: Mention data
            keywords: Matched keywords
        """
        action_dir = (
            self._config.root / "Needs_Action" / "Twitter"
        )
        action_dir.mkdir(parents=True, exist_ok=True)

        mention_id = mention.get("id", "unknown")
        filename = f"TWITTER_MENTION_{mention_id}.md"
        file_path = action_dir / filename

        content = (
            f"---\n"
            f"id: \"{mention_id}\"\n"
            f"type: \"twitter_mention\"\n"
            f"author_id: \"{mention.get('author_id', 'unknown')}\"\n"
            f"keywords: {keywords}\n"
            f"timestamp: \"{datetime.now().isoformat()}\"\n"
            f"action_status: \"new\"\n"
            f"---\n\n"
            f"# Twitter Mention: {mention_id}\n\n"
            f"**Keywords**: {', '.join(keywords)}\n\n"
            f"## Content\n\n"
            f"{mention.get('text', '')}\n\n"
            f"---\n"
            f"*High-priority mention - follow up required*\n"
        )

        file_path.write_text(content)

        self._log_event("action_created", {
            "mention_id": mention_id,
            "keywords": keywords,
        })
