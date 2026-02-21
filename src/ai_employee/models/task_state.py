"""TaskState model - represents the state of an autonomous task in the Ralph Wiggum loop.

Stored as JSON in /Active_Tasks/{task_id}.json.
State transitions: pending -> in_progress -> (paused -> in_progress)* -> completed|failed
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_employee.models.enums import TaskStatus

VALID_COMPLETION_STRATEGIES = ("promise", "file_movement")


@dataclass(frozen=True)
class TaskState:
    """Immutable state of an autonomous task.

    Uses frozen=True to enforce immutability. All state transitions
    return new TaskState instances via helper methods.
    """

    task_id: str
    prompt: str
    iteration: int
    max_iterations: int
    status: TaskStatus
    completion_strategy: str
    completion_promise: str | None
    context: str | None
    requires_approval: bool
    approval_id: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    @classmethod
    def create(
        cls,
        prompt: str,
        completion_strategy: str = "promise",
        completion_promise: str | None = "TASK_COMPLETE",
        max_iterations: int = 10,
    ) -> TaskState:
        """Create a new TaskState with validated defaults.

        Args:
            prompt: Natural language description of the task.
            completion_strategy: Either "promise" or "file_movement".
            completion_promise: String the agent outputs to signal completion.
            max_iterations: Maximum loop iterations before auto-fail.

        Returns:
            New TaskState in PENDING status.

        Raises:
            ValueError: If prompt is empty, max_iterations < 1,
                       or completion_strategy is invalid.
        """
        if not prompt or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        if completion_strategy not in VALID_COMPLETION_STRATEGIES:
            raise ValueError(
                f"completion_strategy must be one of "
                f"{VALID_COMPLETION_STRATEGIES}, got '{completion_strategy}'"
            )

        now = datetime.now()
        return cls(
            task_id=str(uuid.uuid4()),
            prompt=prompt.strip(),
            iteration=1,
            max_iterations=max_iterations,
            status=TaskStatus.PENDING,
            completion_strategy=completion_strategy,
            completion_promise=completion_promise,
            context=None,
            requires_approval=False,
            approval_id=None,
            created_at=now,
            updated_at=now,
            completed_at=None,
        )

    # ─────────────────────────────────────────────────────────────
    # Immutable state transition helpers
    # ─────────────────────────────────────────────────────────────

    def with_status(self, status: TaskStatus) -> TaskState:
        """Return a new TaskState with an updated status."""
        return TaskState(
            task_id=self.task_id,
            prompt=self.prompt,
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            status=status,
            completion_strategy=self.completion_strategy,
            completion_promise=self.completion_promise,
            context=self.context,
            requires_approval=self.requires_approval,
            approval_id=self.approval_id,
            created_at=self.created_at,
            updated_at=datetime.now(),
            completed_at=self.completed_at,
        )

    def with_iteration(self, iteration: int, context: str | None) -> TaskState:
        """Return a new TaskState with updated iteration and context."""
        return TaskState(
            task_id=self.task_id,
            prompt=self.prompt,
            iteration=iteration,
            max_iterations=self.max_iterations,
            status=self.status,
            completion_strategy=self.completion_strategy,
            completion_promise=self.completion_promise,
            context=context,
            requires_approval=self.requires_approval,
            approval_id=self.approval_id,
            created_at=self.created_at,
            updated_at=datetime.now(),
            completed_at=self.completed_at,
        )

    def with_completed(self) -> TaskState:
        """Return a new TaskState marked as completed."""
        now = datetime.now()
        return TaskState(
            task_id=self.task_id,
            prompt=self.prompt,
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            status=TaskStatus.COMPLETED,
            completion_strategy=self.completion_strategy,
            completion_promise=self.completion_promise,
            context=self.context,
            requires_approval=False,
            approval_id=None,
            created_at=self.created_at,
            updated_at=now,
            completed_at=now,
        )

    def with_failed(self, error_message: str) -> TaskState:
        """Return a new TaskState marked as failed with error context."""
        now = datetime.now()
        return TaskState(
            task_id=self.task_id,
            prompt=self.prompt,
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            status=TaskStatus.FAILED,
            completion_strategy=self.completion_strategy,
            completion_promise=self.completion_promise,
            context=error_message,
            requires_approval=False,
            approval_id=None,
            created_at=self.created_at,
            updated_at=now,
            completed_at=now,
        )

    def with_paused(self, approval_id: str) -> TaskState:
        """Return a new TaskState paused for approval."""
        return TaskState(
            task_id=self.task_id,
            prompt=self.prompt,
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            status=TaskStatus.PAUSED,
            completion_strategy=self.completion_strategy,
            completion_promise=self.completion_promise,
            context=self.context,
            requires_approval=True,
            approval_id=approval_id,
            created_at=self.created_at,
            updated_at=datetime.now(),
            completed_at=self.completed_at,
        )

    # ─────────────────────────────────────────────────────────────
    # Properties
    # ─────────────────────────────────────────────────────────────

    @property
    def is_terminal(self) -> bool:
        """Check if the task is in a terminal state (completed or failed)."""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)

    @property
    def can_continue(self) -> bool:
        """Check if the task can continue iterating."""
        return self.status == TaskStatus.IN_PROGRESS

    # ─────────────────────────────────────────────────────────────
    # Serialization
    # ─────────────────────────────────────────────────────────────

    def to_json_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "status": self.status.value,
            "completion_strategy": self.completion_strategy,
            "completion_promise": self.completion_promise,
            "context": self.context,
            "requires_approval": self.requires_approval,
            "approval_id": self.approval_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at
                else None
            ),
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, Any]) -> TaskState:
        """Create a TaskState from a JSON-compatible dictionary.

        Args:
            data: Dictionary with TaskState fields.

        Returns:
            Restored TaskState instance.
        """
        return cls(
            task_id=data["task_id"],
            prompt=data["prompt"],
            iteration=data["iteration"],
            max_iterations=data["max_iterations"],
            status=TaskStatus(data["status"]),
            completion_strategy=data["completion_strategy"],
            completion_promise=data.get("completion_promise"),
            context=data.get("context"),
            requires_approval=data.get("requires_approval", False),
            approval_id=data.get("approval_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
        )

    def to_json(self) -> str:
        """Serialize to a JSON string.

        Returns:
            Indented JSON string representation.
        """
        return json.dumps(self.to_json_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> TaskState:
        """Deserialize from a JSON string.

        Args:
            json_str: JSON string to parse.

        Returns:
            Restored TaskState instance.
        """
        data = json.loads(json_str)
        return cls.from_json_dict(data)

    # ─────────────────────────────────────────────────────────────
    # File operations
    # ─────────────────────────────────────────────────────────────

    def get_filename(self) -> str:
        """Get the filename for this task state.

        Returns:
            Filename in the format {task_id}.json
        """
        return f"{self.task_id}.json"

    def save(self, directory: Path) -> Path:
        """Save the task state to a JSON file.

        Args:
            directory: Directory to save the file in.

        Returns:
            Path to the saved file.
        """
        file_path = directory / self.get_filename()
        file_path.write_text(self.to_json())
        return file_path

    @classmethod
    def load(cls, file_path: Path) -> TaskState | None:
        """Load a task state from a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            TaskState instance, or None if file does not exist.
        """
        if not file_path.exists():
            return None

        json_str = file_path.read_text()
        return cls.from_json(json_str)
