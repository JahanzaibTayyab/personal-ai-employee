"""AuditEntry model for comprehensive audit logging."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class AuditEntry:
    """Represents a single audit log entry.

    Captures all information about an action taken by the AI Employee,
    including actor, target, approval chain, and timing.

    Action types: email_draft, email_send, invoice_create, invoice_post,
    payment_record, post_facebook, post_instagram, post_twitter,
    task_start, task_complete, task_fail, approval_request,
    approval_granted, watcher_start, watcher_stop, watcher_restart,
    briefing_generate, ralph_loop_start, ralph_loop_iterate,
    ralph_loop_complete
    """

    timestamp: datetime
    action_type: str
    actor: str
    target: str
    parameters: dict[str, Any] | None = None
    approval_status: str = "not_required"
    approved_by: str | None = None
    result: str = "success"
    error_message: str | None = None
    correlation_id: str | None = None
    duration_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert AuditEntry to a dictionary for serialization.

        Optional fields with None values are excluded from the output.

        Returns:
            Dictionary representation of the audit entry.
        """
        data: dict[str, Any] = {
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type,
            "actor": self.actor,
            "target": self.target,
            "result": self.result,
            "approval_status": self.approval_status,
        }

        if self.parameters is not None:
            data["parameters"] = self.parameters
        if self.approved_by is not None:
            data["approved_by"] = self.approved_by
        if self.error_message is not None:
            data["error_message"] = self.error_message
        if self.correlation_id is not None:
            data["correlation_id"] = self.correlation_id
        if self.duration_ms is not None:
            data["duration_ms"] = self.duration_ms

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEntry":
        """Create AuditEntry from a dictionary.

        Args:
            data: Dictionary with audit entry data.

        Returns:
            AuditEntry instance.
        """
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            action_type=data["action_type"],
            actor=data["actor"],
            target=data["target"],
            parameters=data.get("parameters"),
            approval_status=data.get("approval_status", "not_required"),
            approved_by=data.get("approved_by"),
            result=data.get("result", "success"),
            error_message=data.get("error_message"),
            correlation_id=data.get("correlation_id"),
            duration_ms=data.get("duration_ms"),
        )

    def to_json(self) -> str:
        """Convert AuditEntry to a JSON string.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "AuditEntry":
        """Create AuditEntry from a JSON string.

        Args:
            json_str: JSON string with audit entry data.

        Returns:
            AuditEntry instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
