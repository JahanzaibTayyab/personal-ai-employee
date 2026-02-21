"""Unit tests for TaskState model."""

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

import pytest

from ai_employee.models.enums import TaskStatus
from ai_employee.models.task_state import TaskState


class TestTaskStateCreation:
    """Tests for creating TaskState instances."""

    def test_create_task_state_with_defaults(self) -> None:
        """Test creating a TaskState with default values."""
        state = TaskState.create(prompt="Process the inbox and draft replies")

        assert state.prompt == "Process the inbox and draft replies"
        assert state.iteration == 1
        assert state.max_iterations == 10
        assert state.status == TaskStatus.PENDING
        assert state.completion_strategy == "promise"
        assert state.completion_promise == "TASK_COMPLETE"
        assert state.context is None
        assert state.requires_approval is False
        assert state.approval_id is None
        assert state.completed_at is None
        # task_id should be a valid UUID string
        UUID(state.task_id)

    def test_create_task_state_with_custom_values(self) -> None:
        """Test creating a TaskState with custom configuration."""
        state = TaskState.create(
            prompt="Move files to Done folder",
            completion_strategy="file_movement",
            completion_promise=None,
            max_iterations=5,
        )

        assert state.prompt == "Move files to Done folder"
        assert state.max_iterations == 5
        assert state.completion_strategy == "file_movement"
        assert state.completion_promise is None

    def test_create_generates_unique_ids(self) -> None:
        """Test that each TaskState gets a unique task_id."""
        state1 = TaskState.create(prompt="Task 1")
        state2 = TaskState.create(prompt="Task 2")

        assert state1.task_id != state2.task_id

    def test_create_sets_timestamps(self) -> None:
        """Test that created_at and updated_at are set on creation."""
        before = datetime.now()
        state = TaskState.create(prompt="Test task")
        after = datetime.now()

        assert before <= state.created_at <= after
        assert before <= state.updated_at <= after


class TestTaskStateValidation:
    """Tests for TaskState validation."""

    def test_empty_prompt_raises_error(self) -> None:
        """Test that an empty prompt raises ValueError."""
        with pytest.raises(ValueError, match="prompt"):
            TaskState.create(prompt="")

    def test_whitespace_only_prompt_raises_error(self) -> None:
        """Test that a whitespace-only prompt raises ValueError."""
        with pytest.raises(ValueError, match="prompt"):
            TaskState.create(prompt="   ")

    def test_max_iterations_must_be_positive(self) -> None:
        """Test that max_iterations must be positive."""
        with pytest.raises(ValueError, match="max_iterations"):
            TaskState.create(prompt="Test", max_iterations=0)

    def test_max_iterations_negative_raises_error(self) -> None:
        """Test that negative max_iterations raises ValueError."""
        with pytest.raises(ValueError, match="max_iterations"):
            TaskState.create(prompt="Test", max_iterations=-1)

    def test_invalid_completion_strategy_raises_error(self) -> None:
        """Test that an invalid completion_strategy raises ValueError."""
        with pytest.raises(ValueError, match="completion_strategy"):
            TaskState.create(prompt="Test", completion_strategy="invalid")


class TestTaskStateSerialization:
    """Tests for TaskState JSON serialization."""

    def test_to_json_dict(self) -> None:
        """Test converting TaskState to JSON-serializable dict."""
        state = TaskState.create(prompt="Test serialization")
        data = state.to_json_dict()

        assert data["task_id"] == state.task_id
        assert data["prompt"] == "Test serialization"
        assert data["iteration"] == 1
        assert data["max_iterations"] == 10
        assert data["status"] == "pending"
        assert data["completion_strategy"] == "promise"
        assert data["completion_promise"] == "TASK_COMPLETE"
        assert data["context"] is None
        assert data["requires_approval"] is False
        assert data["approval_id"] is None
        assert data["completed_at"] is None
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

    def test_from_json_dict(self) -> None:
        """Test creating TaskState from JSON dict."""
        original = TaskState.create(prompt="Roundtrip test")
        data = original.to_json_dict()

        restored = TaskState.from_json_dict(data)

        assert restored.task_id == original.task_id
        assert restored.prompt == original.prompt
        assert restored.iteration == original.iteration
        assert restored.max_iterations == original.max_iterations
        assert restored.status == original.status
        assert restored.completion_strategy == original.completion_strategy
        assert restored.completion_promise == original.completion_promise
        assert restored.context == original.context
        assert restored.requires_approval == original.requires_approval

    def test_to_json_string(self) -> None:
        """Test converting TaskState to JSON string."""
        state = TaskState.create(prompt="JSON string test")
        json_str = state.to_json()

        parsed = json.loads(json_str)
        assert parsed["prompt"] == "JSON string test"

    def test_from_json_string(self) -> None:
        """Test creating TaskState from JSON string."""
        state = TaskState.create(prompt="From JSON string")
        json_str = state.to_json()

        restored = TaskState.from_json(json_str)
        assert restored.prompt == "From JSON string"
        assert restored.task_id == state.task_id

    def test_roundtrip_with_all_fields(self) -> None:
        """Test full roundtrip with all optional fields populated."""
        now = datetime.now()
        state = TaskState(
            task_id="test-uuid-1234",
            prompt="Full roundtrip",
            iteration=3,
            max_iterations=15,
            status=TaskStatus.PAUSED,
            completion_strategy="file_movement",
            completion_promise=None,
            context="Step 3 context here",
            requires_approval=True,
            approval_id="approval_12345",
            created_at=now,
            updated_at=now,
            completed_at=None,
        )

        json_str = state.to_json()
        restored = TaskState.from_json(json_str)

        assert restored.task_id == "test-uuid-1234"
        assert restored.iteration == 3
        assert restored.max_iterations == 15
        assert restored.status == TaskStatus.PAUSED
        assert restored.completion_strategy == "file_movement"
        assert restored.completion_promise is None
        assert restored.context == "Step 3 context here"
        assert restored.requires_approval is True
        assert restored.approval_id == "approval_12345"


class TestTaskStateFileOperations:
    """Tests for TaskState file persistence."""

    def test_save_to_file(self, tmp_path: Path) -> None:
        """Test saving TaskState to a JSON file."""
        active_tasks = tmp_path / "Active_Tasks"
        active_tasks.mkdir()

        state = TaskState.create(prompt="Save test")
        file_path = state.save(active_tasks)

        assert file_path.exists()
        assert file_path.name == f"{state.task_id}.json"
        assert file_path.parent == active_tasks

        content = json.loads(file_path.read_text())
        assert content["prompt"] == "Save test"

    def test_load_from_file(self, tmp_path: Path) -> None:
        """Test loading TaskState from a JSON file."""
        active_tasks = tmp_path / "Active_Tasks"
        active_tasks.mkdir()

        original = TaskState.create(prompt="Load test")
        file_path = original.save(active_tasks)

        loaded = TaskState.load(file_path)

        assert loaded.task_id == original.task_id
        assert loaded.prompt == "Load test"

    def test_load_nonexistent_file_returns_none(self, tmp_path: Path) -> None:
        """Test that loading from a nonexistent file returns None."""
        result = TaskState.load(tmp_path / "nonexistent.json")
        assert result is None

    def test_get_filename(self) -> None:
        """Test that get_filename returns correct pattern."""
        state = TaskState.create(prompt="Filename test")
        filename = state.get_filename()

        assert filename == f"{state.task_id}.json"


class TestTaskStateTransitions:
    """Tests for state transition helpers."""

    def test_with_status_creates_new_instance(self) -> None:
        """Test that with_status returns a new TaskState (immutability)."""
        original = TaskState.create(prompt="Immutability test")
        updated = original.with_status(TaskStatus.IN_PROGRESS)

        assert updated.status == TaskStatus.IN_PROGRESS
        assert original.status == TaskStatus.PENDING
        assert updated is not original

    def test_with_status_preserves_fields(self) -> None:
        """Test that with_status preserves all other fields."""
        original = TaskState.create(
            prompt="Preserve fields",
            max_iterations=7,
            completion_strategy="file_movement",
        )
        updated = original.with_status(TaskStatus.IN_PROGRESS)

        assert updated.task_id == original.task_id
        assert updated.prompt == original.prompt
        assert updated.max_iterations == 7
        assert updated.completion_strategy == "file_movement"

    def test_with_status_updates_timestamp(self) -> None:
        """Test that with_status updates updated_at."""
        original = TaskState.create(prompt="Timestamp test")
        original_updated_at = original.updated_at

        updated = original.with_status(TaskStatus.IN_PROGRESS)

        assert updated.updated_at >= original_updated_at

    def test_with_iteration_creates_new_instance(self) -> None:
        """Test that with_iteration returns a new TaskState."""
        original = TaskState.create(prompt="Iteration test")
        updated = original.with_iteration(2, context="Step 2 context")

        assert updated.iteration == 2
        assert updated.context == "Step 2 context"
        assert original.iteration == 1
        assert original.context is None

    def test_with_completed_sets_completed_at(self) -> None:
        """Test that with_completed sets completed_at and status."""
        state = TaskState.create(prompt="Complete test")
        completed = state.with_completed()

        assert completed.status == TaskStatus.COMPLETED
        assert completed.completed_at is not None
        assert state.completed_at is None

    def test_with_failed_sets_context_error(self) -> None:
        """Test that with_failed sets error context and status."""
        state = TaskState.create(prompt="Fail test")
        failed = state.with_failed("Something went wrong")

        assert failed.status == TaskStatus.FAILED
        assert failed.context == "Something went wrong"
        assert failed.completed_at is not None

    def test_with_paused_sets_approval_id(self) -> None:
        """Test that with_paused sets approval fields."""
        state = TaskState.create(prompt="Pause test")
        paused = state.with_paused("approval_123")

        assert paused.status == TaskStatus.PAUSED
        assert paused.requires_approval is True
        assert paused.approval_id == "approval_123"

    def test_is_terminal_for_completed(self) -> None:
        """Test that completed is a terminal state."""
        state = TaskState.create(prompt="Terminal test")
        completed = state.with_completed()

        assert completed.is_terminal is True

    def test_is_terminal_for_failed(self) -> None:
        """Test that failed is a terminal state."""
        state = TaskState.create(prompt="Terminal test")
        failed = state.with_failed("Error")

        assert failed.is_terminal is True

    def test_is_not_terminal_for_active_states(self) -> None:
        """Test that pending, in_progress, paused are not terminal."""
        state = TaskState.create(prompt="Non-terminal test")

        assert state.is_terminal is False

        in_progress = state.with_status(TaskStatus.IN_PROGRESS)
        assert in_progress.is_terminal is False

        paused = state.with_paused("approval_456")
        assert paused.is_terminal is False

    def test_can_continue_for_in_progress(self) -> None:
        """Test that an in_progress task can continue."""
        state = TaskState.create(prompt="Continue test")
        in_progress = state.with_status(TaskStatus.IN_PROGRESS)

        assert in_progress.can_continue is True

    def test_cannot_continue_when_paused(self) -> None:
        """Test that a paused task cannot continue."""
        state = TaskState.create(prompt="Cannot continue")
        paused = state.with_paused("approval_789")

        assert paused.can_continue is False

    def test_cannot_continue_when_completed(self) -> None:
        """Test that a completed task cannot continue."""
        state = TaskState.create(prompt="Cannot continue")
        completed = state.with_completed()

        assert completed.can_continue is False
