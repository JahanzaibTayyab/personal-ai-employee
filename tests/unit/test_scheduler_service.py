"""Unit tests for SchedulerService."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.scheduled_task import (
    ScheduledTask,
    TaskType,
    MissedStrategy,
    create_daily_briefing_task,
    create_weekly_audit_task,
)


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault structure."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Schedules").mkdir()
    (vault / "Briefings").mkdir()
    (vault / "Logs").mkdir()
    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create VaultConfig for testing."""
    return VaultConfig(vault_path)


class TestSchedulerService:
    """Tests for SchedulerService class."""

    def test_service_initialization(self, vault_config: VaultConfig) -> None:
        """Test SchedulerService initializes correctly."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)
        assert service is not None

    def test_add_task_creates_file(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test adding a task creates a schedule file."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Test Task",
            schedule="0 9 * * *",  # Daily at 9 AM
            task_type=TaskType.CUSTOM,
            action_config={"command": "echo hello"},
        )

        result = service.add_task(task)

        assert result is True

        # Verify file created
        schedule_files = list((vault_path / "Schedules").glob("*.md"))
        assert len(schedule_files) == 1

    def test_add_one_time_task(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test adding a one-time scheduled task."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        task = ScheduledTask.create(
            name="One Time Task",
            schedule=future_time,
            task_type=TaskType.CUSTOM,
        )

        result = service.add_task(task)
        assert result is True

    def test_remove_task(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test removing a task deletes the file."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Task To Remove",
            schedule="0 8 * * *",
            task_type=TaskType.BRIEFING,
        )

        service.add_task(task)

        # Verify task exists
        assert len(list((vault_path / "Schedules").glob("*.md"))) == 1

        # Remove the task
        result = service.remove_task(task.id)
        assert result is True

        # Verify task removed
        assert len(list((vault_path / "Schedules").glob("*.md"))) == 0

    def test_remove_nonexistent_task(self, vault_config: VaultConfig) -> None:
        """Test removing a task that doesn't exist returns False."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)
        result = service.remove_task("nonexistent_task")

        assert result is False

    def test_get_all_tasks(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test getting all scheduled tasks."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        # Add multiple tasks
        task1 = ScheduledTask.create(
            name="Task One",
            schedule="0 8 * * *",
            task_type=TaskType.BRIEFING,
        )
        task2 = ScheduledTask.create(
            name="Task Two",
            schedule="0 21 * * 0",
            task_type=TaskType.AUDIT,
        )

        service.add_task(task1)
        service.add_task(task2)

        tasks = service.get_all_tasks()
        assert len(tasks) == 2

    def test_get_task_by_id(self, vault_config: VaultConfig) -> None:
        """Test getting a specific task by ID."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Find Me",
            schedule="30 10 * * *",
            task_type=TaskType.CUSTOM,
        )
        service.add_task(task)

        found = service.get_task(task.id)
        assert found is not None
        assert found.name == "Find Me"

    def test_get_nonexistent_task(self, vault_config: VaultConfig) -> None:
        """Test getting a task that doesn't exist returns None."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)
        found = service.get_task("nonexistent")

        assert found is None

    def test_enable_task(self, vault_config: VaultConfig) -> None:
        """Test enabling a task."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Toggle Task",
            schedule="0 12 * * *",
            task_type=TaskType.CUSTOM,
        )
        task.enabled = False
        service.add_task(task)

        result = service.enable_task(task.id)
        assert result is True

        updated = service.get_task(task.id)
        assert updated is not None
        assert updated.enabled is True

    def test_disable_task(self, vault_config: VaultConfig) -> None:
        """Test disabling a task."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Disable Me",
            schedule="0 14 * * *",
            task_type=TaskType.CUSTOM,
        )
        service.add_task(task)

        result = service.disable_task(task.id)
        assert result is True

        updated = service.get_task(task.id)
        assert updated is not None
        assert updated.enabled is False


class TestTaskExecution:
    """Tests for task execution."""

    def test_run_task_success(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test running a task successfully."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Run Me",
            schedule="0 8 * * *",
            task_type=TaskType.UPDATE_DASHBOARD,
        )
        service.add_task(task)

        # Mock the task executor
        with patch.object(service, "_execute_action") as mock_exec:
            mock_exec.return_value = {"success": True, "message": "Dashboard updated"}
            result = service.run_task(task.id)

        assert result["success"] is True

    def test_run_disabled_task(self, vault_config: VaultConfig) -> None:
        """Test running a disabled task is blocked."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Disabled Task",
            schedule="0 8 * * *",
            task_type=TaskType.CUSTOM,
        )
        task.enabled = False
        service.add_task(task)

        result = service.run_task(task.id)
        assert result["success"] is False
        assert "disabled" in result.get("error", "").lower()

    def test_run_nonexistent_task(self, vault_config: VaultConfig) -> None:
        """Test running a task that doesn't exist."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)
        result = service.run_task("nonexistent")

        assert result["success"] is False
        assert "not found" in result.get("error", "").lower()

    def test_run_task_updates_last_run(
        self, vault_config: VaultConfig
    ) -> None:
        """Test running a task updates last_run timestamp."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Track Time",
            schedule="0 10 * * *",
            task_type=TaskType.UPDATE_DASHBOARD,
        )
        service.add_task(task)

        with patch.object(service, "_execute_action") as mock_exec:
            mock_exec.return_value = {"success": True}
            service.run_task(task.id)

        updated = service.get_task(task.id)
        assert updated is not None
        assert updated.last_run is not None


class TestMissedScheduleHandling:
    """Tests for missed schedule handling (FR-029)."""

    def test_get_missed_tasks(self, vault_config: VaultConfig) -> None:
        """Test getting tasks that missed their schedule."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        # Create task with past next_run
        task = ScheduledTask.create(
            name="Missed Task",
            schedule="0 8 * * *",
            task_type=TaskType.BRIEFING,
        )
        task.next_run = datetime.now() - timedelta(hours=2)
        service.add_task(task)

        missed = service.get_missed_tasks()
        assert len(missed) >= 1

    def test_handle_missed_skip(self, vault_config: VaultConfig) -> None:
        """Test handling missed task with SKIP strategy."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Skip Task",
            schedule="0 8 * * *",
            task_type=TaskType.BRIEFING,
            missed_strategy=MissedStrategy.SKIP,
        )
        task.next_run = datetime.now() - timedelta(hours=1)
        service.add_task(task)

        with patch.object(service, "_execute_action") as mock_exec:
            service.handle_missed_task(task.id)
            # With SKIP, the action should not be executed
            mock_exec.assert_not_called()

    def test_handle_missed_run_immediately(
        self, vault_config: VaultConfig
    ) -> None:
        """Test handling missed task with RUN_IMMEDIATELY strategy."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Run Now Task",
            schedule="0 8 * * *",
            task_type=TaskType.UPDATE_DASHBOARD,
            missed_strategy=MissedStrategy.RUN_IMMEDIATELY,
        )
        task.next_run = datetime.now() - timedelta(hours=1)
        service.add_task(task)

        with patch.object(service, "_execute_action") as mock_exec:
            mock_exec.return_value = {"success": True}
            service.handle_missed_task(task.id)
            # With RUN_IMMEDIATELY, the action should be executed
            mock_exec.assert_called_once()


class TestTimezoneSupport:
    """Tests for timezone support (FR-030)."""

    def test_task_with_timezone(self, vault_config: VaultConfig) -> None:
        """Test creating task with specific timezone."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Pacific Task",
            schedule="0 9 * * *",
            task_type=TaskType.BRIEFING,
            timezone="America/Los_Angeles",
        )
        service.add_task(task)

        found = service.get_task(task.id)
        assert found is not None
        assert found.timezone == "America/Los_Angeles"

    def test_default_local_timezone(self, vault_config: VaultConfig) -> None:
        """Test default timezone is local."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Local Task",
            schedule="0 9 * * *",
            task_type=TaskType.BRIEFING,
        )
        service.add_task(task)

        found = service.get_task(task.id)
        assert found is not None
        assert found.timezone == "local"


class TestTaskExecutionLogging:
    """Tests for task execution logging (FR-028)."""

    def test_execution_creates_log_entry(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test task execution creates a log entry."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Logged Task",
            schedule="0 8 * * *",
            task_type=TaskType.UPDATE_DASHBOARD,
        )
        service.add_task(task)

        with patch.object(service, "_execute_action") as mock_exec:
            mock_exec.return_value = {"success": True, "message": "Done"}
            service.run_task(task.id)

        # Verify log file created
        log_files = list((vault_path / "Logs").glob("scheduler_*.log"))
        assert len(log_files) >= 1


class TestBriefingGeneration:
    """Tests for briefing generation task (T081)."""

    def test_run_briefing_task(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test running a briefing generation task."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = create_daily_briefing_task(hour=8, minute=0)
        service.add_task(task)

        with patch.object(service, "_generate_briefing") as mock_briefing:
            mock_briefing.return_value = "# Daily Briefing\n\nNo pending items."
            result = service.run_task(task.id)

        assert result["success"] is True

    def test_briefing_output_location(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test briefing is saved to correct location."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = create_daily_briefing_task()
        service.add_task(task)

        with patch.object(service, "_generate_briefing") as mock_briefing:
            mock_briefing.return_value = "# Briefing"
            service.run_task(task.id)

        # Verify briefing file created
        briefing_files = list((vault_path / "Briefings").glob("*.md"))
        assert len(briefing_files) >= 1


class TestWeeklyAudit:
    """Tests for weekly audit task (T082)."""

    def test_run_audit_task(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test running a weekly audit task."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = create_weekly_audit_task(day_of_week=0, hour=21)
        service.add_task(task)

        with patch.object(service, "_generate_audit") as mock_audit:
            mock_audit.return_value = {"items_processed": 10, "success_rate": 95}
            result = service.run_task(task.id)

        assert result["success"] is True


class TestSchedulerServiceErrors:
    """Tests for SchedulerService error handling."""

    def test_add_duplicate_task(self, vault_config: VaultConfig) -> None:
        """Test adding a task with duplicate ID."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Original",
            schedule="0 8 * * *",
            task_type=TaskType.CUSTOM,
        )
        service.add_task(task)

        # Adding same ID should update, not error
        task2 = ScheduledTask.create(
            name="Original",  # Same name = same ID
            schedule="0 9 * * *",
            task_type=TaskType.CUSTOM,
        )
        result = service.add_task(task2)
        assert result is True

        # Should have only one task
        tasks = service.get_all_tasks()
        assert len(tasks) == 1

    def test_invalid_task_type_execution(
        self, vault_config: VaultConfig
    ) -> None:
        """Test executing task with unknown type handles gracefully."""
        from ai_employee.services.scheduler import SchedulerService

        service = SchedulerService(vault_config)

        task = ScheduledTask.create(
            name="Unknown Type",
            schedule="0 8 * * *",
            task_type=TaskType.CUSTOM,
            action_config={"unknown_field": "value"},
        )
        service.add_task(task)

        # Should not raise, but return error
        result = service.run_task(task.id)
        # Custom tasks without proper handler should fail gracefully
        assert "error" in result or result["success"] is True
