"""Watcher Event model - detection events from watchers."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SourceType(str, Enum):
    """Source type of the watcher."""

    FILESYSTEM = "filesystem"
    GMAIL = "gmail"


class EventType(str, Enum):
    """Type of event detected."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    ERROR = "error"
    STARTED = "started"
    STOPPED = "stopped"


@dataclass
class WatcherEvent:
    """A detection event from a watcher.

    Stored in /Logs/watcher_YYYY-MM-DD.log as JSON lines format.
    """

    timestamp: datetime
    source_type: SourceType
    event_type: EventType
    identifier: str
    metadata: dict = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert to JSON string for log file."""
        data: dict[str, Any] = {
            "timestamp": self.timestamp.isoformat(),
            "source_type": self.source_type.value,
            "event_type": self.event_type.value,
            "identifier": self.identifier,
        }

        if self.metadata:
            data["metadata"] = self.metadata

        return json.dumps(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data: dict[str, Any] = {
            "timestamp": self.timestamp.isoformat(),
            "source_type": self.source_type.value,
            "event_type": self.event_type.value,
            "identifier": self.identifier,
        }

        if self.metadata:
            data["metadata"] = self.metadata

        return data

    @classmethod
    def from_json(cls, json_str: str) -> "WatcherEvent":
        """Create WatcherEvent from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WatcherEvent":
        """Create WatcherEvent from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source_type=SourceType(data["source_type"]),
            event_type=EventType(data["event_type"]),
            identifier=data["identifier"],
            metadata=data.get("metadata", {}),
        )
