"""Activity Log Entry model - records AI actions taken."""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    """Type of action performed."""

    PROCESS = "process"
    MOVE = "move"
    UPDATE = "update"
    ERROR = "error"


class Outcome(str, Enum):
    """Result of the action."""

    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"


@dataclass
class ActivityLogEntry:
    """A record of an AI action taken.

    Stored in /Logs/claude_YYYY-MM-DD.log as JSON lines format.
    """

    timestamp: datetime
    action_type: ActionType
    item_id: str
    outcome: Outcome
    duration_ms: int | None = None
    details: str | None = None

    def to_json(self) -> str:
        """Convert to JSON string for log file."""
        data: dict[str, Any] = {
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type.value,
            "item_id": self.item_id,
            "outcome": self.outcome.value,
        }

        if self.duration_ms is not None:
            data["duration_ms"] = self.duration_ms
        if self.details is not None:
            data["details"] = self.details

        return json.dumps(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data: dict[str, Any] = {
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type.value,
            "item_id": self.item_id,
            "outcome": self.outcome.value,
        }

        if self.duration_ms is not None:
            data["duration_ms"] = self.duration_ms
        if self.details is not None:
            data["details"] = self.details

        return data

    @classmethod
    def from_json(cls, json_str: str) -> "ActivityLogEntry":
        """Create ActivityLogEntry from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActivityLogEntry":
        """Create ActivityLogEntry from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            action_type=ActionType(data["action_type"]),
            item_id=data["item_id"],
            outcome=Outcome(data["outcome"]),
            duration_ms=data.get("duration_ms"),
            details=data.get("details"),
        )
