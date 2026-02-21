"""Unit tests for RalphWiggumService."""

import json
from pathlib import Path

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.enums import TaskStatus
from ai_employee.models.task_state import TaskState
from ai_employee.services.ralph_wiggum import (
    ApprovalPendingError,
    InvalidPromptError,
    InvalidStateError,
    MaxIterationsExceededError,
    RalphWiggumService,
    TaskAlreadyActiveError,
    TaskNotFoundError,
)


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault structure with Active_Tasks folder."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Active_Tasks").mkdir()
    (vault / "Done").mkdir()
    (vault / "Logs").mkdir()
    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create VaultConfig for testing."""
    return VaultConfig(vault_path)


@pytest.fixture
def service(vault_config: VaultConfig) -> RalphWiggumService:
    """Create RalphWiggumService instance for testing."""
    return RalphWiggumService(vault_config)


class TestStartTask:
    """Tests for starting a new autonomous task."""

    def test_start_task_creates_state_file(
        self, service: RalphWiggumService, vault_path: Path
    ) -> None:
        """Test that start_task creates a JSON state file in Active_Tasks."""
        state = service.start_task(prompt="Process inbox items")

        assert state.status == TaskStatus.IN_PROGRESS
        assert state.prompt == "Process inbox items"

        task_file = vault_path / "Active_Tasks" / f"{state.task_id}.json"
        assert task_file.exists()

    def test_start_task_with_default_values(
        self, service: RalphWiggumService
    ) -> None:
        """Test start_task with default completion settings."""
        state = service.start_task(prompt="Default task")

        assert state.completion_strategy == "promise"
        assert state.completion_promise == "TASK_COMPLETE"
        assert state.max_iterations == 10
        assert state.iteration == 1

    def test_start_task_with_custom_values(
        self, service: RalphWiggumService
    ) -> None:
        """Test start_task with custom completion strategy."""
        state = service.start_task(
            prompt="Move files",
            completion_strategy="file_movement",
            completion_promise=None,
            max_iterations=5,
        )

        assert state.completion_strategy == "file_movement"
        assert state.completion_promise is None
        assert state.max_iterations == 5

    def test_start_task_raises_on_empty_prompt(
        self, service: RalphWiggumService
    ) -> None:
        """Test that empty prompt raises InvalidPromptError."""
        with pytest.raises(InvalidPromptError, match="prompt"):
            service.start_task(prompt="")

    def test_start_task_raises_on_whitespace_prompt(
        self, service: RalphWiggumService
    ) -> None:
        """Test that whitespace-only prompt raises InvalidPromptError."""
        with pytest.raises(InvalidPromptError, match="prompt"):
            service.start_task(prompt="   \n\t  ")

    def test_start_task_raises_when_task_already_active(
        self, service: RalphWiggumService
    ) -> None:
        """Test that starting a second task raises TaskAlreadyActiveError."""
        service.start_task(prompt="First task")

        with pytest.raises(TaskAlreadyActiveError, match="already active"):
            service.start_task(prompt="Second task")

    def test_start_task_allowed_after_previous_completed(
        self, service: RalphWiggumService
    ) -> None:
        """Test starting a new task after previous one completes."""
        first = service.start_task(prompt="First task")
        service.complete_task(first.task_id)

        second = service.start_task(prompt="Second task")
        assert second.status == TaskStatus.IN_PROGRESS


class TestGetTaskState:
    """Tests for retrieving task state."""

    def test_get_task_state_by_id(
        self, service: RalphWiggumService
    ) -> None:
        """Test getting a task state by its ID."""
        created = service.start_task(prompt="Get me")

        retrieved = service.get_task_state(created.task_id)

        assert retrieved is not None
        assert retrieved.task_id == created.task_id
        assert retrieved.prompt == "Get me"

    def test_get_task_state_not_found(
        self, service: RalphWiggumService
    ) -> None:
        """Test getting a nonexistent task returns None."""
        result = service.get_task_state("nonexistent-uuid")
        assert result is None

    def test_get_active_task_returns_in_progress(
        self, service: RalphWiggumService
    ) -> None:
        """Test that get_active_task returns in_progress task."""
        created = service.start_task(prompt="Active task")

        active = service.get_active_task()

        assert active is not None
        assert active.task_id == created.task_id
        assert active.status == TaskStatus.IN_PROGRESS

    def test_get_active_task_returns_paused(
        self, service: RalphWiggumService
    ) -> None:
        """Test that get_active_task returns paused task."""
        created = service.start_task(prompt="Will be paused")
        service.pause_task(created.task_id, approval_id="approval_123")

        active = service.get_active_task()

        assert active is not None
        assert active.status == TaskStatus.PAUSED

    def test_get_active_task_returns_none_when_all_completed(
        self, service: RalphWiggumService
    ) -> None:
        """Test that get_active_task returns None when no active tasks."""
        created = service.start_task(prompt="Done task")
        service.complete_task(created.task_id)

        active = service.get_active_task()
        assert active is None

    def test_get_active_task_returns_none_when_empty(
        self, service: RalphWiggumService
    ) -> None:
        """Test that get_active_task returns None when no tasks exist."""
        active = service.get_active_task()
        assert active is None


class TestPauseTask:
    """Tests for pausing a task (approval workflow)."""

    def test_pause_in_progress_task(
        self, service: RalphWiggumService
    ) -> None:
        """Test pausing an in_progress task."""
        created = service.start_task(prompt="Pausable task")
        paused = service.pause_task(created.task_id, approval_id="approval_999")

        assert paused.status == TaskStatus.PAUSED
        assert paused.requires_approval is True
        assert paused.approval_id == "approval_999"

    def test_pause_task_persists_state(
        self, service: RalphWiggumService
    ) -> None:
        """Test that pausing persists the updated state to disk."""
        created = service.start_task(prompt="Persist pause")
        service.pause_task(created.task_id, approval_id="approval_001")

        reloaded = service.get_task_state(created.task_id)
        assert reloaded is not None
        assert reloaded.status == TaskStatus.PAUSED

    def test_pause_nonexistent_task_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test pausing a nonexistent task raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            service.pause_task("nonexistent", approval_id="approval_xxx")

    def test_pause_completed_task_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test pausing a completed task raises TaskNotFoundError.

        Completed tasks are moved to Done, so they are no longer
        in Active_Tasks and cannot be found.
        """
        created = service.start_task(prompt="Completed task")
        service.complete_task(created.task_id)

        with pytest.raises(TaskNotFoundError):
            service.pause_task(created.task_id, approval_id="approval_yyy")

    def test_pause_already_paused_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test pausing an already-paused task raises InvalidStateError."""
        created = service.start_task(prompt="Already paused")
        service.pause_task(created.task_id, approval_id="approval_aaa")

        with pytest.raises(InvalidStateError, match="Cannot pause"):
            service.pause_task(created.task_id, approval_id="approval_bbb")


class TestResumeTask:
    """Tests for resuming a paused task."""

    def test_resume_paused_task(
        self, service: RalphWiggumService
    ) -> None:
        """Test resuming a paused task sets it to in_progress."""
        created = service.start_task(prompt="Resume me")
        service.pause_task(created.task_id, approval_id="approval_111")

        resumed = service.resume_task(created.task_id)

        assert resumed.status == TaskStatus.IN_PROGRESS
        assert resumed.requires_approval is False
        assert resumed.approval_id is None

    def test_resume_persists_state(
        self, service: RalphWiggumService
    ) -> None:
        """Test that resuming persists the updated state to disk."""
        created = service.start_task(prompt="Persist resume")
        service.pause_task(created.task_id, approval_id="approval_222")
        service.resume_task(created.task_id)

        reloaded = service.get_task_state(created.task_id)
        assert reloaded is not None
        assert reloaded.status == TaskStatus.IN_PROGRESS

    def test_resume_nonexistent_task_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test resuming a nonexistent task raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            service.resume_task("nonexistent")

    def test_resume_in_progress_task_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test resuming an already in_progress task raises InvalidStateError."""
        created = service.start_task(prompt="Not paused")

        with pytest.raises(InvalidStateError, match="Cannot resume"):
            service.resume_task(created.task_id)


class TestCompleteTask:
    """Tests for completing a task."""

    def test_complete_in_progress_task(
        self, service: RalphWiggumService
    ) -> None:
        """Test completing an in_progress task."""
        created = service.start_task(prompt="Complete me")
        completed = service.complete_task(created.task_id)

        assert completed.status == TaskStatus.COMPLETED
        assert completed.completed_at is not None

    def test_complete_moves_to_done(
        self, service: RalphWiggumService, vault_path: Path
    ) -> None:
        """Test that completing a task moves the file to Done folder."""
        created = service.start_task(prompt="Move to done")
        service.complete_task(created.task_id)

        # File should no longer be in Active_Tasks
        active_file = vault_path / "Active_Tasks" / f"{created.task_id}.json"
        assert not active_file.exists()

        # File should be in Done
        done_file = vault_path / "Done" / f"{created.task_id}.json"
        assert done_file.exists()

    def test_complete_nonexistent_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test completing a nonexistent task raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            service.complete_task("nonexistent")

    def test_complete_already_completed_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test completing an already completed task raises InvalidStateError."""
        created = service.start_task(prompt="Already done")
        service.complete_task(created.task_id)

        with pytest.raises(TaskNotFoundError):
            service.complete_task(created.task_id)


class TestFailTask:
    """Tests for failing a task."""

    def test_fail_in_progress_task(
        self, service: RalphWiggumService
    ) -> None:
        """Test failing an in_progress task."""
        created = service.start_task(prompt="Fail me")
        failed = service.fail_task(created.task_id, error_message="Something broke")

        assert failed.status == TaskStatus.FAILED
        assert failed.context == "Something broke"
        assert failed.completed_at is not None

    def test_fail_moves_to_done(
        self, service: RalphWiggumService, vault_path: Path
    ) -> None:
        """Test that failing a task moves the file to Done folder."""
        created = service.start_task(prompt="Fail and move")
        service.fail_task(created.task_id, error_message="Error occurred")

        active_file = vault_path / "Active_Tasks" / f"{created.task_id}.json"
        assert not active_file.exists()

        done_file = vault_path / "Done" / f"{created.task_id}.json"
        assert done_file.exists()

    def test_fail_paused_task(
        self, service: RalphWiggumService
    ) -> None:
        """Test failing a paused task."""
        created = service.start_task(prompt="Fail paused")
        service.pause_task(created.task_id, approval_id="approval_333")
        failed = service.fail_task(created.task_id, error_message="Timed out")

        assert failed.status == TaskStatus.FAILED

    def test_fail_nonexistent_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test failing a nonexistent task raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            service.fail_task("nonexistent", error_message="Error")


class TestIncrementIteration:
    """Tests for incrementing the iteration counter."""

    def test_increment_iteration(
        self, service: RalphWiggumService
    ) -> None:
        """Test incrementing iteration with context."""
        created = service.start_task(prompt="Iterate me")
        updated = service.increment_iteration(
            created.task_id, context="Processed step 1"
        )

        assert updated.iteration == 2
        assert updated.context == "Processed step 1"

    def test_increment_persists_state(
        self, service: RalphWiggumService
    ) -> None:
        """Test that incrementing persists state to disk."""
        created = service.start_task(prompt="Persist increment")
        service.increment_iteration(created.task_id, context="Step 1 done")

        reloaded = service.get_task_state(created.task_id)
        assert reloaded is not None
        assert reloaded.iteration == 2
        assert reloaded.context == "Step 1 done"

    def test_increment_multiple_times(
        self, service: RalphWiggumService
    ) -> None:
        """Test incrementing multiple times."""
        created = service.start_task(prompt="Multi-step", max_iterations=5)

        for i in range(4):
            service.increment_iteration(
                created.task_id, context=f"Step {i + 1}"
            )

        state = service.get_task_state(created.task_id)
        assert state is not None
        assert state.iteration == 5

    def test_increment_exceeds_max_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test that exceeding max_iterations raises MaxIterationsExceededError."""
        created = service.start_task(prompt="Exceed limit", max_iterations=3)

        service.increment_iteration(created.task_id, context="Step 1")
        service.increment_iteration(created.task_id, context="Step 2")

        with pytest.raises(MaxIterationsExceededError, match="3"):
            service.increment_iteration(created.task_id, context="Step 3")

    def test_increment_nonexistent_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test incrementing nonexistent task raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            service.increment_iteration("nonexistent", context="N/A")

    def test_increment_completed_task_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test incrementing completed task raises InvalidStateError."""
        created = service.start_task(prompt="Completed")
        service.complete_task(created.task_id)

        with pytest.raises(TaskNotFoundError):
            service.increment_iteration(created.task_id, context="N/A")

    def test_increment_paused_task_raises_error(
        self, service: RalphWiggumService
    ) -> None:
        """Test incrementing paused task raises ApprovalPendingError."""
        created = service.start_task(prompt="Paused")
        service.pause_task(created.task_id, approval_id="approval_444")

        with pytest.raises(ApprovalPendingError):
            service.increment_iteration(created.task_id, context="N/A")


class TestErrorClasses:
    """Tests for custom error classes."""

    def test_task_already_active_error(self) -> None:
        """Test TaskAlreadyActiveError message."""
        error = TaskAlreadyActiveError("Task is already active")
        assert str(error) == "Task is already active"

    def test_invalid_prompt_error(self) -> None:
        """Test InvalidPromptError message."""
        error = InvalidPromptError("Empty prompt not allowed")
        assert str(error) == "Empty prompt not allowed"

    def test_task_not_found_error(self) -> None:
        """Test TaskNotFoundError message."""
        error = TaskNotFoundError("Task abc not found")
        assert str(error) == "Task abc not found"

    def test_invalid_state_error(self) -> None:
        """Test InvalidStateError message."""
        error = InvalidStateError("Cannot pause completed task")
        assert str(error) == "Cannot pause completed task"

    def test_approval_pending_error(self) -> None:
        """Test ApprovalPendingError message."""
        error = ApprovalPendingError("Task is awaiting approval")
        assert str(error) == "Task is awaiting approval"

    def test_max_iterations_exceeded_error(self) -> None:
        """Test MaxIterationsExceededError message."""
        error = MaxIterationsExceededError("Exceeded 10 iterations")
        assert str(error) == "Exceeded 10 iterations"

    def test_error_hierarchy(self) -> None:
        """Test that all errors inherit from base RalphWiggumError."""
        from ai_employee.services.ralph_wiggum import RalphWiggumError

        assert issubclass(TaskAlreadyActiveError, RalphWiggumError)
        assert issubclass(InvalidPromptError, RalphWiggumError)
        assert issubclass(TaskNotFoundError, RalphWiggumError)
        assert issubclass(InvalidStateError, RalphWiggumError)
        assert issubclass(ApprovalPendingError, RalphWiggumError)
        assert issubclass(MaxIterationsExceededError, RalphWiggumError)
