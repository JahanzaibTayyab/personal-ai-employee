"""Integration tests for the Ralph Wiggum autonomous loop flow.

Tests the full lifecycle of tasks through the Ralph Wiggum service,
including state persistence, file movement, and multi-step workflows.
"""

import json
from pathlib import Path

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.enums import TaskStatus
from ai_employee.models.task_state import TaskState
from ai_employee.services.ralph_wiggum import (
    MaxIterationsExceededError,
    RalphWiggumService,
    TaskAlreadyActiveError,
)


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a full vault structure for integration testing."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Active_Tasks").mkdir()
    (vault / "Done").mkdir()
    (vault / "Logs").mkdir()
    (vault / "Pending_Approval").mkdir()
    (vault / "Approved").mkdir()
    (vault / "Rejected").mkdir()
    (vault / "Inbox").mkdir()
    (vault / "Needs_Action").mkdir()
    (vault / "Drop").mkdir()
    (vault / "Quarantine").mkdir()
    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create VaultConfig for integration testing."""
    return VaultConfig(vault_path)


@pytest.fixture
def service(vault_config: VaultConfig) -> RalphWiggumService:
    """Create RalphWiggumService for integration testing."""
    return RalphWiggumService(vault_config)


class TestFullTaskLifecycle:
    """Integration tests for complete task lifecycles."""

    def test_happy_path_task_completion(
        self, service: RalphWiggumService, vault_path: Path
    ) -> None:
        """Test complete task lifecycle: start -> iterate -> complete."""
        # Start the task
        state = service.start_task(
            prompt="Process inbox and draft replies",
            max_iterations=5,
        )
        assert state.status == TaskStatus.IN_PROGRESS
        task_id = state.task_id

        # Verify file exists in Active_Tasks
        active_file = vault_path / "Active_Tasks" / f"{task_id}.json"
        assert active_file.exists()

        # Simulate iterations
        service.increment_iteration(task_id, context="Read 3 inbox items")
        service.increment_iteration(task_id, context="Drafted reply for item 1")
        service.increment_iteration(task_id, context="Drafted reply for item 2")

        # Verify iteration count
        current = service.get_task_state(task_id)
        assert current is not None
        assert current.iteration == 4

        # Complete the task
        completed = service.complete_task(task_id)
        assert completed.status == TaskStatus.COMPLETED
        assert completed.completed_at is not None

        # Verify file moved to Done
        assert not active_file.exists()
        done_file = vault_path / "Done" / f"{task_id}.json"
        assert done_file.exists()

        # Verify Done file content is valid
        done_data = json.loads(done_file.read_text())
        assert done_data["status"] == "completed"
        assert done_data["iteration"] == 4

    def test_task_with_approval_pause(
        self, service: RalphWiggumService, vault_path: Path
    ) -> None:
        """Test task lifecycle with pause for approval."""
        # Start task
        state = service.start_task(prompt="Send important email to client")
        task_id = state.task_id

        # Progress a couple iterations
        service.increment_iteration(task_id, context="Drafted email content")

        # Pause for approval
        paused = service.pause_task(task_id, approval_id="approval_email_001")
        assert paused.status == TaskStatus.PAUSED
        assert paused.requires_approval is True

        # Verify active task is still found
        active = service.get_active_task()
        assert active is not None
        assert active.status == TaskStatus.PAUSED

        # Simulate approval granted - resume
        resumed = service.resume_task(task_id)
        assert resumed.status == TaskStatus.IN_PROGRESS
        assert resumed.requires_approval is False

        # Continue and complete
        service.increment_iteration(task_id, context="Sent the email")
        service.complete_task(task_id)

        # Verify in Done
        done_file = vault_path / "Done" / f"{task_id}.json"
        assert done_file.exists()

    def test_task_failure_lifecycle(
        self, service: RalphWiggumService, vault_path: Path
    ) -> None:
        """Test task lifecycle that ends in failure."""
        state = service.start_task(prompt="Process payment for vendor")
        task_id = state.task_id

        service.increment_iteration(task_id, context="Validated payment info")

        # Task fails
        failed = service.fail_task(
            task_id, error_message="Payment gateway unavailable"
        )
        assert failed.status == TaskStatus.FAILED
        assert failed.context == "Payment gateway unavailable"

        # Verify moved to Done (even failures go to Done for audit)
        done_file = vault_path / "Done" / f"{task_id}.json"
        assert done_file.exists()

        done_data = json.loads(done_file.read_text())
        assert done_data["status"] == "failed"

    def test_max_iterations_exceeded(
        self, service: RalphWiggumService
    ) -> None:
        """Test that exceeding max_iterations raises error and can be failed."""
        state = service.start_task(
            prompt="Long-running analysis", max_iterations=3
        )
        task_id = state.task_id

        service.increment_iteration(task_id, context="Step 1")
        service.increment_iteration(task_id, context="Step 2")

        with pytest.raises(MaxIterationsExceededError):
            service.increment_iteration(task_id, context="Step 3 - too many")

        # Fail the task after exceeding iterations
        failed = service.fail_task(
            task_id, error_message="Max iterations exceeded (3)"
        )
        assert failed.status == TaskStatus.FAILED

    def test_sequential_tasks(
        self, service: RalphWiggumService
    ) -> None:
        """Test running tasks sequentially (one at a time)."""
        # First task
        first = service.start_task(prompt="First task")
        service.complete_task(first.task_id)

        # Second task
        second = service.start_task(prompt="Second task")
        service.complete_task(second.task_id)

        # Third task
        third = service.start_task(prompt="Third task")
        service.fail_task(third.task_id, error_message="Intentional failure")

        # All should be in Done
        assert service.get_active_task() is None

    def test_cannot_run_concurrent_tasks(
        self, service: RalphWiggumService
    ) -> None:
        """Test that only one task can be active at a time."""
        service.start_task(prompt="Active task")

        with pytest.raises(TaskAlreadyActiveError):
            service.start_task(prompt="Another task")


class TestStatePersistence:
    """Integration tests for state persistence across service instances."""

    def test_state_survives_service_restart(
        self, vault_config: VaultConfig
    ) -> None:
        """Test that task state persists across service restarts."""
        # Start task with first service instance
        service1 = RalphWiggumService(vault_config)
        state = service1.start_task(prompt="Persistent task")
        task_id = state.task_id
        service1.increment_iteration(task_id, context="Step 1")

        # Create new service instance (simulating restart)
        service2 = RalphWiggumService(vault_config)
        retrieved = service2.get_task_state(task_id)

        assert retrieved is not None
        assert retrieved.task_id == task_id
        assert retrieved.iteration == 2
        assert retrieved.context == "Step 1"

    def test_active_task_detected_after_restart(
        self, vault_config: VaultConfig
    ) -> None:
        """Test that active task is detected after service restart."""
        service1 = RalphWiggumService(vault_config)
        service1.start_task(prompt="Active on restart")

        service2 = RalphWiggumService(vault_config)
        active = service2.get_active_task()

        assert active is not None
        assert active.prompt == "Active on restart"

    def test_completed_task_not_detected_as_active(
        self, vault_config: VaultConfig
    ) -> None:
        """Test that completed tasks are not returned as active."""
        service1 = RalphWiggumService(vault_config)
        state = service1.start_task(prompt="Will be completed")
        service1.complete_task(state.task_id)

        service2 = RalphWiggumService(vault_config)
        active = service2.get_active_task()

        assert active is None


class TestFileMovement:
    """Integration tests for file-based completion strategy."""

    def test_file_movement_strategy_state(
        self, service: RalphWiggumService
    ) -> None:
        """Test that file_movement strategy is stored correctly."""
        state = service.start_task(
            prompt="Move files from Inbox to Done",
            completion_strategy="file_movement",
            completion_promise=None,
        )

        assert state.completion_strategy == "file_movement"
        assert state.completion_promise is None

        # Retrieve and verify
        retrieved = service.get_task_state(state.task_id)
        assert retrieved is not None
        assert retrieved.completion_strategy == "file_movement"

    def test_promise_strategy_state(
        self, service: RalphWiggumService
    ) -> None:
        """Test that promise strategy stores completion_promise."""
        state = service.start_task(
            prompt="Process and signal",
            completion_strategy="promise",
            completion_promise="ALL_DONE",
        )

        assert state.completion_strategy == "promise"
        assert state.completion_promise == "ALL_DONE"


class TestEdgeCases:
    """Integration tests for edge cases."""

    def test_task_with_single_iteration(
        self, service: RalphWiggumService
    ) -> None:
        """Test a task that completes on first iteration (no increment)."""
        state = service.start_task(prompt="Quick task")
        completed = service.complete_task(state.task_id)

        assert completed.iteration == 1
        assert completed.status == TaskStatus.COMPLETED

    def test_pause_resume_multiple_times(
        self, service: RalphWiggumService
    ) -> None:
        """Test pausing and resuming the same task multiple times."""
        state = service.start_task(prompt="Multi-pause task")
        task_id = state.task_id

        # First pause/resume
        service.pause_task(task_id, approval_id="approval_a")
        service.resume_task(task_id)

        # Second pause/resume
        service.increment_iteration(task_id, context="More work")
        service.pause_task(task_id, approval_id="approval_b")
        service.resume_task(task_id)

        # Complete
        completed = service.complete_task(task_id)
        assert completed.status == TaskStatus.COMPLETED
        assert completed.iteration == 2

    def test_large_context_survives_roundtrip(
        self, service: RalphWiggumService
    ) -> None:
        """Test that large context strings survive serialization."""
        state = service.start_task(prompt="Large context")
        large_context = "x" * 10000
        service.increment_iteration(state.task_id, context=large_context)

        retrieved = service.get_task_state(state.task_id)
        assert retrieved is not None
        assert retrieved.context == large_context

    def test_special_characters_in_prompt(
        self, service: RalphWiggumService
    ) -> None:
        """Test that special characters in prompt are handled correctly."""
        prompt = 'Process "important" items with special chars: <>&\n\ttabs'
        state = service.start_task(prompt=prompt)

        retrieved = service.get_task_state(state.task_id)
        assert retrieved is not None
        assert retrieved.prompt == prompt
