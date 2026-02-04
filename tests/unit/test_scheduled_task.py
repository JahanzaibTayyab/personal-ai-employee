"""Unit tests for ScheduledTask model."""

from datetime import datetime, timedelta

import pytest

from ai_employee.models.scheduled_task import (
    MissedStrategy,
    ScheduledTask,
    TaskType,
    create_daily_briefing_task,
    create_weekly_audit_task,
)


class TestScheduledTask:
    """Tests for ScheduledTask dataclass."""

    def test_create_cron_task(self) -> None:
        """Test creating a cron-scheduled task."""
        task = ScheduledTask.create(
            name="Daily Test",
            schedule="0 8 * * *",
            task_type=TaskType.BRIEFING,
        )

        assert task.name == "Daily Test"
        assert task.schedule == "0 8 * * *"
        assert task.is_cron() is True
        assert task.is_one_time() is False
        assert task.enabled is True

    def test_create_one_time_task(self) -> None:
        """Test creating a one-time scheduled task."""
        future_time = (datetime.now() + timedelta(days=1)).isoformat()
        task = ScheduledTask.create(
            name="One Time Task",
            schedule=future_time,
            task_type=TaskType.CUSTOM,
        )

        assert task.is_cron() is False
        assert task.is_one_time() is True

    def test_create_with_custom_config(self) -> None:
        """Test creating task with custom action config."""
        task = ScheduledTask.create(
            name="Custom Task",
            schedule="0 12 * * *",
            task_type=TaskType.CUSTOM,
            action_config={"command": "test_command", "args": ["--verbose"]},
            timezone="America/New_York",
            missed_strategy=MissedStrategy.SKIP,
        )

        assert task.timezone == "America/New_York"
        assert task.missed_strategy == MissedStrategy.SKIP
        assert task.action["command"] == "test_command"
        assert task.action["type"] == "custom"

    def test_get_one_time_datetime(self) -> None:
        """Test getting datetime for one-time schedule."""
        future_time = datetime.now() + timedelta(days=1)
        task = ScheduledTask.create(
            name="One Time",
            schedule=future_time.isoformat(),
            task_type=TaskType.CUSTOM,
        )

        result = task.get_one_time_datetime()
        assert result is not None
        assert abs((result - future_time).total_seconds()) < 1

    def test_get_one_time_datetime_cron(self) -> None:
        """Test get_one_time_datetime returns None for cron."""
        task = ScheduledTask.create(
            name="Cron Task",
            schedule="0 8 * * *",
            task_type=TaskType.BRIEFING,
        )

        assert task.get_one_time_datetime() is None

    def test_to_frontmatter(self) -> None:
        """Test conversion to frontmatter dictionary."""
        task = ScheduledTask.create(
            name="Test Task",
            schedule="0 9 * * 1-5",
            task_type=TaskType.UPDATE_DASHBOARD,
        )

        fm = task.to_frontmatter()

        assert fm["name"] == "Test Task"
        assert fm["schedule"] == "0 9 * * 1-5"
        assert fm["enabled"] is True
        assert fm["missed_strategy"] == "run_immediately"

    def test_from_frontmatter(self) -> None:
        """Test creation from frontmatter dictionary."""
        fm = {
            "id": "schedule_test",
            "name": "Restored Task",
            "schedule": "0 8 * * *",
            "action": {"type": "briefing"},
            "enabled": False,
            "timezone": "UTC",
            "missed_strategy": "queue",
            "created_at": "2026-02-03T10:00:00",
            "last_run": "2026-02-03T08:00:00",
        }

        task = ScheduledTask.from_frontmatter(fm)

        assert task.id == "schedule_test"
        assert task.name == "Restored Task"
        assert task.enabled is False
        assert task.missed_strategy == MissedStrategy.QUEUE
        assert task.last_run is not None

    def test_get_filename(self) -> None:
        """Test filename generation."""
        task = ScheduledTask.create(
            name="My Task",
            schedule="0 8 * * *",
            task_type=TaskType.BRIEFING,
        )

        assert task.get_filename() == "schedule_my_task.md"

    def test_validation_invalid_cron(self) -> None:
        """Test validation rejects invalid cron expression."""
        with pytest.raises(ValueError, match="Invalid cron expression"):
            ScheduledTask(
                id="invalid",
                name="Invalid",
                schedule="invalid cron",  # Not a valid cron
                action={"type": "briefing"},
                created_at=datetime.now(),
            )

    def test_validation_invalid_datetime(self) -> None:
        """Test validation rejects invalid datetime format."""
        with pytest.raises(ValueError, match="Invalid datetime format"):
            ScheduledTask(
                id="invalid",
                name="Invalid",
                schedule="not-a-datetime",  # Not a valid datetime
                action={"type": "custom"},
                created_at=datetime.now(),
            )

    def test_valid_cron_expressions(self) -> None:
        """Test various valid cron expressions."""
        valid_crons = [
            "0 8 * * *",  # Daily at 8am
            "*/15 * * * *",  # Every 15 minutes
            "0 9 * * 1-5",  # Weekdays at 9am
            "0 0 1 * *",  # First of month at midnight
            "30 14 * * 0",  # Sundays at 2:30pm
        ]

        for cron in valid_crons:
            task = ScheduledTask.create(
                name="Test",
                schedule=cron,
                task_type=TaskType.CUSTOM,
            )
            assert task.schedule == cron


class TestDailyBriefingTask:
    """Tests for create_daily_briefing_task helper."""

    def test_default_briefing(self) -> None:
        """Test default daily briefing task."""
        task = create_daily_briefing_task()

        assert task.name == "Daily Briefing"
        assert task.schedule == "0 8 * * *"
        assert task.action["type"] == "briefing"
        assert task.action["include_pending_approvals"] is True

    def test_custom_time_briefing(self) -> None:
        """Test daily briefing with custom time."""
        task = create_daily_briefing_task(hour=9, minute=30)

        assert task.schedule == "30 9 * * *"

    def test_briefing_with_timezone(self) -> None:
        """Test daily briefing with custom timezone."""
        task = create_daily_briefing_task(timezone="Europe/London")

        assert task.timezone == "Europe/London"


class TestWeeklyAuditTask:
    """Tests for create_weekly_audit_task helper."""

    def test_default_audit(self) -> None:
        """Test default weekly audit task."""
        task = create_weekly_audit_task()

        assert task.name == "Weekly Audit"
        assert task.schedule == "0 21 * * 0"  # Sunday 9pm
        assert task.action["type"] == "audit"
        assert task.action["analyze_completed_items"] is True

    def test_custom_day_audit(self) -> None:
        """Test weekly audit on different day."""
        task = create_weekly_audit_task(day_of_week=5, hour=18)  # Friday 6pm

        assert task.schedule == "0 18 * * 5"


class TestMissedStrategy:
    """Tests for MissedStrategy enum."""

    def test_all_strategies_exist(self) -> None:
        """Test all required strategies are defined."""
        assert MissedStrategy.SKIP.value == "skip"
        assert MissedStrategy.RUN_IMMEDIATELY.value == "run_immediately"
        assert MissedStrategy.QUEUE.value == "queue"


class TestTaskType:
    """Tests for TaskType enum."""

    def test_all_types_exist(self) -> None:
        """Test all required task types are defined."""
        assert TaskType.BRIEFING.value == "briefing"
        assert TaskType.AUDIT.value == "audit"
        assert TaskType.UPDATE_DASHBOARD.value == "update_dashboard"
        assert TaskType.CHECK_APPROVALS.value == "check_approvals"
        assert TaskType.CUSTOM.value == "custom"
