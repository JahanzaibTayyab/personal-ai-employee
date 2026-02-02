"""Base watcher abstract class."""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from ai_employee.models.watcher_event import EventType, SourceType, WatcherEvent
from ai_employee.utils.jsonl_logger import JsonlLogger


class BaseWatcher(ABC):
    """Abstract base class for watchers.

    Watchers monitor sources (filesystem, gmail) for events and
    create action items in the vault.
    """

    def __init__(self, vault_path: Path, source_type: SourceType):
        """Initialize the watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            source_type: Type of source being watched
        """
        self.vault_path = vault_path
        self.source_type = source_type
        self.running = False

        # Set up event logger
        logs_dir = vault_path / "Logs"
        self.event_logger = JsonlLogger[WatcherEvent](
            logs_dir=logs_dir,
            prefix="watcher",
            serializer=lambda e: e.to_json(),
            deserializer=WatcherEvent.from_json,
        )

    @property
    def needs_action_path(self) -> Path:
        """Path to the Needs_Action folder."""
        return self.vault_path / "Needs_Action"

    @property
    def drop_path(self) -> Path:
        """Path to the Drop folder (for filesystem watcher)."""
        return self.vault_path / "Drop"

    @property
    def quarantine_path(self) -> Path:
        """Path to the Quarantine folder."""
        return self.vault_path / "Quarantine"

    def log_event(
        self,
        event_type: EventType,
        identifier: str,
        metadata: dict | None = None,
    ) -> None:
        """Log a watcher event.

        Args:
            event_type: Type of event
            identifier: File path or message ID
            metadata: Optional additional data
        """
        event = WatcherEvent(
            timestamp=datetime.now(),
            source_type=self.source_type,
            event_type=event_type,
            identifier=identifier,
            metadata=metadata or {},
        )
        self.event_logger.log(event)

    @abstractmethod
    def start(self) -> None:
        """Start watching for events."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop watching for events."""
        pass

    @abstractmethod
    def process_event(self, event: WatcherEvent) -> None:
        """Process a detected event.

        Args:
            event: The event to process
        """
        pass
