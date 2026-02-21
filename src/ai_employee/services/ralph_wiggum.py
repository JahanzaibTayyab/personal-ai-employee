"""Ralph Wiggum autonomous execution loop service.

Manages the lifecycle of autonomous tasks that run in a multi-step loop
without constant human intervention. Only one task can be active at a time.

Task files are stored as JSON in /Active_Tasks/{task_id}.json and moved
to /Done/ upon completion or failure.
"""

from __future__ import annotations

from pathlib import Path

from ai_employee.config import VaultConfig
from ai_employee.models.enums import TaskStatus
from ai_employee.models.task_state import TaskState

# ─────────────────────────────────────────────────────────────
# Error hierarchy
# ─────────────────────────────────────────────────────────────


class RalphWiggumError(Exception):
    """Base exception for Ralph Wiggum service."""


class TaskAlreadyActiveError(RalphWiggumError):
    """Raised when attempting to start a task while another is active."""


class InvalidPromptError(RalphWiggumError):
    """Raised when the task prompt is empty or invalid."""


class TaskNotFoundError(RalphWiggumError):
    """Raised when a task ID does not match any known task."""


class InvalidStateError(RalphWiggumError):
    """Raised when a state transition is invalid for the current status."""


class ApprovalPendingError(RalphWiggumError):
    """Raised when an operation requires the task to not be paused for approval."""


class MaxIterationsExceededError(RalphWiggumError):
    """Raised when a task exceeds its configured max_iterations."""


# ─────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────


class RalphWiggumService:
    """Service for managing the Ralph Wiggum autonomous execution loop.

    Responsibilities:
    - Start, pause, resume, complete, and fail tasks
    - Enforce single-active-task constraint
    - Persist task state as JSON files in the vault
    - Move completed/failed tasks to Done folder
    """

    def __init__(self, vault_config: VaultConfig) -> None:
        """Initialize with vault configuration.

        Args:
            vault_config: VaultConfig with vault root path.
        """
        self._config = vault_config
        self._active_tasks_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _active_tasks_dir(self) -> Path:
        """Path to the Active_Tasks directory."""
        return self._config.root / "Active_Tasks"

    @property
    def _done_dir(self) -> Path:
        """Path to the Done directory."""
        return self._config.done

    # ─────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────

    def _list_active_task_files(self) -> list[Path]:
        """List all JSON task files in Active_Tasks directory."""
        if not self._active_tasks_dir.exists():
            return []
        return sorted(self._active_tasks_dir.glob("*.json"))

    def _load_task_from_active(self, task_id: str) -> TaskState | None:
        """Load a task state from Active_Tasks by ID.

        Args:
            task_id: The UUID of the task.

        Returns:
            TaskState if found, None otherwise.
        """
        file_path = self._active_tasks_dir / f"{task_id}.json"
        return TaskState.load(file_path)

    def _save_task_to_active(self, state: TaskState) -> Path:
        """Save a task state to the Active_Tasks directory.

        Args:
            state: The TaskState to persist.

        Returns:
            Path to the saved file.
        """
        return state.save(self._active_tasks_dir)

    def _move_to_done(self, state: TaskState) -> Path:
        """Move a task file from Active_Tasks to Done.

        Args:
            state: The TaskState to archive.

        Returns:
            Path to the file in Done.
        """
        src = self._active_tasks_dir / state.get_filename()
        dst = self._done_dir / state.get_filename()

        # Write the updated state to Done
        state.save(self._done_dir)

        # Remove from Active_Tasks
        if src.exists():
            src.unlink()

        return dst

    def _require_active_task(self, task_id: str) -> TaskState:
        """Load a task from Active_Tasks or raise TaskNotFoundError.

        Args:
            task_id: The UUID of the task.

        Returns:
            The loaded TaskState.

        Raises:
            TaskNotFoundError: If no task with that ID exists in Active_Tasks.
        """
        state = self._load_task_from_active(task_id)
        if state is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return state

    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────

    def start_task(
        self,
        prompt: str,
        completion_strategy: str = "promise",
        completion_promise: str | None = "TASK_COMPLETE",
        max_iterations: int = 10,
    ) -> TaskState:
        """Start a new autonomous task.

        Creates a TaskState in IN_PROGRESS status and persists it to disk.
        Only one task may be active at a time.

        Args:
            prompt: Natural language description of what to accomplish.
            completion_strategy: Either "promise" or "file_movement".
            completion_promise: Token the agent outputs to signal completion.
            max_iterations: Maximum loop iterations before auto-fail.

        Returns:
            The newly created TaskState in IN_PROGRESS status.

        Raises:
            InvalidPromptError: If prompt is empty or whitespace-only.
            TaskAlreadyActiveError: If another task is already active.
        """
        if not prompt or not prompt.strip():
            raise InvalidPromptError(
                "Task prompt must be a non-empty string"
            )

        # Check for existing active task
        active = self.get_active_task()
        if active is not None:
            raise TaskAlreadyActiveError(
                f"Task {active.task_id} is already active "
                f"(status: {active.status.value})"
            )

        # Create and immediately transition to IN_PROGRESS
        state = TaskState.create(
            prompt=prompt,
            completion_strategy=completion_strategy,
            completion_promise=completion_promise,
            max_iterations=max_iterations,
        )
        in_progress = state.with_status(TaskStatus.IN_PROGRESS)

        self._save_task_to_active(in_progress)
        return in_progress

    def get_task_state(self, task_id: str) -> TaskState | None:
        """Get the current state of a task by ID.

        Searches Active_Tasks first, then Done.

        Args:
            task_id: The UUID of the task.

        Returns:
            TaskState if found, None otherwise.
        """
        # Check Active_Tasks first
        state = self._load_task_from_active(task_id)
        if state is not None:
            return state

        # Check Done folder
        done_path = self._done_dir / f"{task_id}.json"
        return TaskState.load(done_path)

    def get_active_task(self) -> TaskState | None:
        """Get the currently active task (in_progress or paused).

        Returns:
            The active TaskState, or None if no task is active.
        """
        for task_file in self._list_active_task_files():
            state = TaskState.load(task_file)
            if state is not None and state.status in (
                TaskStatus.IN_PROGRESS,
                TaskStatus.PAUSED,
            ):
                return state
        return None

    def pause_task(self, task_id: str, approval_id: str) -> TaskState:
        """Pause a task for human approval.

        Args:
            task_id: The UUID of the task to pause.
            approval_id: The ID of the approval request.

        Returns:
            The updated TaskState in PAUSED status.

        Raises:
            TaskNotFoundError: If the task does not exist.
            InvalidStateError: If the task is not in IN_PROGRESS status.
        """
        state = self._require_active_task(task_id)

        if state.status != TaskStatus.IN_PROGRESS:
            raise InvalidStateError(
                f"Cannot pause task in '{state.status.value}' status. "
                f"Task must be in 'in_progress' status."
            )

        paused = state.with_paused(approval_id)
        self._save_task_to_active(paused)
        return paused

    def resume_task(self, task_id: str) -> TaskState:
        """Resume a paused task after approval.

        Args:
            task_id: The UUID of the task to resume.

        Returns:
            The updated TaskState in IN_PROGRESS status.

        Raises:
            TaskNotFoundError: If the task does not exist.
            InvalidStateError: If the task is not in PAUSED status.
        """
        state = self._require_active_task(task_id)

        if state.status != TaskStatus.PAUSED:
            raise InvalidStateError(
                f"Cannot resume task in '{state.status.value}' status. "
                f"Task must be in 'paused' status."
            )

        # Clear approval fields and set back to IN_PROGRESS
        resumed = TaskState(
            task_id=state.task_id,
            prompt=state.prompt,
            iteration=state.iteration,
            max_iterations=state.max_iterations,
            status=TaskStatus.IN_PROGRESS,
            completion_strategy=state.completion_strategy,
            completion_promise=state.completion_promise,
            context=state.context,
            requires_approval=False,
            approval_id=None,
            created_at=state.created_at,
            updated_at=state.updated_at,
            completed_at=state.completed_at,
        )

        self._save_task_to_active(resumed)
        return resumed

    def complete_task(self, task_id: str) -> TaskState:
        """Mark a task as completed and move to Done.

        Args:
            task_id: The UUID of the task to complete.

        Returns:
            The updated TaskState in COMPLETED status.

        Raises:
            TaskNotFoundError: If the task does not exist in Active_Tasks.
            InvalidStateError: If the task is not in an active state.
        """
        state = self._require_active_task(task_id)

        if state.status not in (TaskStatus.IN_PROGRESS, TaskStatus.PAUSED):
            raise InvalidStateError(
                f"Cannot complete task in '{state.status.value}' status."
            )

        completed = state.with_completed()
        self._move_to_done(completed)
        return completed

    def fail_task(self, task_id: str, error_message: str) -> TaskState:
        """Mark a task as failed and move to Done.

        Args:
            task_id: The UUID of the task to fail.
            error_message: Description of the failure.

        Returns:
            The updated TaskState in FAILED status.

        Raises:
            TaskNotFoundError: If the task does not exist in Active_Tasks.
        """
        state = self._require_active_task(task_id)

        failed = state.with_failed(error_message)
        self._move_to_done(failed)
        return failed

    def increment_iteration(
        self, task_id: str, context: str | None = None
    ) -> TaskState:
        """Increment the iteration counter for a task.

        Args:
            task_id: The UUID of the task.
            context: Optional context string describing what happened
                     in this iteration.

        Returns:
            The updated TaskState with incremented iteration.

        Raises:
            TaskNotFoundError: If the task does not exist.
            ApprovalPendingError: If the task is paused for approval.
            MaxIterationsExceededError: If incrementing would exceed
                                        max_iterations.
        """
        state = self._require_active_task(task_id)

        if state.status == TaskStatus.PAUSED:
            raise ApprovalPendingError(
                f"Task {task_id} is paused pending approval "
                f"(approval_id: {state.approval_id})"
            )

        if state.status != TaskStatus.IN_PROGRESS:
            raise InvalidStateError(
                f"Cannot increment iteration for task in "
                f"'{state.status.value}' status."
            )

        next_iteration = state.iteration + 1
        if next_iteration > state.max_iterations:
            raise MaxIterationsExceededError(
                f"Task {task_id} would exceed max_iterations "
                f"({state.max_iterations})"
            )

        updated = state.with_iteration(next_iteration, context)
        self._save_task_to_active(updated)
        return updated
