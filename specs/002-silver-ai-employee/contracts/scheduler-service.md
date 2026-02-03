# Scheduler Service Contract

**Service**: `SchedulerService`
**Module**: `src/ai_employee/services/scheduler.py`

## Overview

The Scheduler Service manages cron-style and one-time scheduled tasks using APScheduler. It handles recurring tasks like daily briefings and supports configurable missed schedule handling.

## Interface

```python
from pathlib import Path
from datetime import datetime
from ai_employee.models.scheduled_task import ScheduledTask, MissedStrategy

class SchedulerService:
    """Cron-based task scheduling service (FR-026 to FR-030)."""

    def __init__(
        self,
        vault_config: VaultConfig,
        timezone: str = "local",
    ) -> None:
        """
        Initialize scheduler service.

        Args:
            vault_config: Vault configuration
            timezone: Default timezone for schedules (FR-030)
        """

    # ─────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """
        Start the scheduler.

        Side Effects:
            - Loads all enabled tasks from /Schedules/
            - Registers tasks with APScheduler
            - Checks for missed schedules
            - Begins background scheduling
        """

    def stop(self) -> None:
        """
        Stop the scheduler gracefully.

        Side Effects:
            - Completes any running tasks
            - Saves scheduler state
            - Shuts down APScheduler
        """

    # ─────────────────────────────────────────────────────────────
    # Task Management (FR-026, FR-027)
    # ─────────────────────────────────────────────────────────────

    def create_recurring_task(
        self,
        name: str,
        cron_expression: str,
        action: dict,
        timezone: str | None = None,
        missed_strategy: MissedStrategy = MissedStrategy.RUN_IMMEDIATELY,
    ) -> ScheduledTask:
        """
        Create a recurring task with cron schedule (FR-026).

        Args:
            name: Human-readable task name
            cron_expression: Cron syntax (e.g., "0 8 * * *")
            action: Action configuration dict
            timezone: Task-specific timezone (default: service timezone)
            missed_strategy: How to handle missed runs (FR-029)

        Returns:
            Created ScheduledTask

        Side Effects:
            - Creates task file in /Schedules/
            - Registers with APScheduler

        Cron Expression Format:
            minute hour day_of_month month day_of_week
            "0 8 * * *" = Daily at 8:00 AM
            "0 21 * * 0" = Weekly Sunday at 9:00 PM
            "0 0 1 * *" = Monthly on 1st at midnight
        """

    def create_one_time_task(
        self,
        name: str,
        run_at: datetime,
        action: dict,
        timezone: str | None = None,
    ) -> ScheduledTask:
        """
        Create a one-time scheduled task (FR-027).

        Args:
            name: Task name
            run_at: Specific datetime to run
            action: Action configuration
            timezone: Timezone for run_at

        Returns:
            Created ScheduledTask

        Side Effects:
            - Creates task file in /Schedules/
            - Registers with APScheduler for one-time execution
        """

    def update_task(
        self,
        task_id: str,
        **updates,
    ) -> ScheduledTask:
        """
        Update an existing scheduled task.

        Args:
            task_id: Task identifier
            **updates: Fields to update

        Returns:
            Updated ScheduledTask

        Side Effects:
            - Updates task file
            - Re-registers with APScheduler if schedule changed
        """

    def delete_task(self, task_id: str) -> None:
        """
        Delete a scheduled task.

        Args:
            task_id: Task to delete

        Side Effects:
            - Removes from APScheduler
            - Deletes task file from /Schedules/
        """

    def enable_task(self, task_id: str) -> None:
        """Enable a disabled task."""

    def disable_task(self, task_id: str) -> None:
        """Disable a task without deleting it."""

    # ─────────────────────────────────────────────────────────────
    # Execution (FR-028, FR-029)
    # ─────────────────────────────────────────────────────────────

    def execute_task(
        self,
        task: ScheduledTask,
    ) -> bool:
        """
        Execute a scheduled task.

        Args:
            task: Task to execute

        Returns:
            True if execution succeeded

        Side Effects:
            - Runs the task action
            - Updates last_run timestamp
            - Calculates next_run
            - Logs execution (FR-028)
        """

    def handle_missed_schedules(self) -> list[ScheduledTask]:
        """
        Handle tasks that missed their schedule (FR-029).

        Returns:
            List of tasks that were handled

        Side Effects:
            - Based on missed_strategy:
                - SKIP: Log and move to next schedule
                - RUN_IMMEDIATELY: Execute now
                - QUEUE: Add to execution queue
        """

    # ─────────────────────────────────────────────────────────────
    # Query
    # ─────────────────────────────────────────────────────────────

    def get_all_tasks(self) -> list[ScheduledTask]:
        """Get all scheduled tasks."""

    def get_enabled_tasks(self) -> list[ScheduledTask]:
        """Get only enabled tasks."""

    def get_task_by_id(self, task_id: str) -> ScheduledTask | None:
        """Get task by ID."""

    def get_upcoming_tasks(
        self,
        hours: int = 24,
    ) -> list[tuple[ScheduledTask, datetime]]:
        """
        Get tasks scheduled to run within specified hours.

        Args:
            hours: Look-ahead window

        Returns:
            List of (task, next_run_time) tuples
        """

    def get_scheduler_status(self) -> dict:
        """
        Get scheduler status for Dashboard.

        Returns:
            {
                "running": True,
                "total_tasks": 5,
                "enabled_tasks": 4,
                "next_task": {"name": "...", "run_at": "..."},
                "recent_executions": [...]
            }
        """

    # ─────────────────────────────────────────────────────────────
    # Built-in Tasks
    # ─────────────────────────────────────────────────────────────

    def setup_default_tasks(self) -> None:
        """
        Create default scheduled tasks.

        Tasks:
            - Daily Briefing (8:00 AM) - User Story 6
            - Weekly Audit (Sunday 9:00 PM) - User Story 6
            - Approval Expiration Check (every hour)
            - Dashboard Update (every 15 minutes)
        """
```

## APScheduler Integration

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

class APSchedulerWrapper:
    """Wrapper around APScheduler for task management."""

    def __init__(self, db_path: Path) -> None:
        """
        Initialize APScheduler with SQLite persistence.

        Args:
            db_path: Path to SQLite database for job storage
        """
        self.scheduler = BackgroundScheduler(
            jobstores={
                'default': SQLAlchemyJobStore(
                    url=f'sqlite:///{db_path}'
                )
            },
            job_defaults={
                'coalesce': True,  # Combine missed runs
                'max_instances': 1,  # Prevent overlapping
                'misfire_grace_time': 600,  # 10 min grace
            }
        )

    def add_cron_job(
        self,
        task_id: str,
        cron_expression: str,
        func: Callable,
        timezone: str,
    ) -> None:
        """Add a cron-triggered job."""
        # Parse cron expression
        minute, hour, day, month, day_of_week = cron_expression.split()

        self.scheduler.add_job(
            func,
            CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=timezone,
            ),
            id=task_id,
            replace_existing=True,
        )

    def add_date_job(
        self,
        task_id: str,
        run_at: datetime,
        func: Callable,
    ) -> None:
        """Add a one-time job."""
        self.scheduler.add_job(
            func,
            DateTrigger(run_date=run_at),
            id=task_id,
            replace_existing=True,
        )
```

## Task File Structure

```markdown
---
id: "schedule_daily_briefing"
name: "Daily Briefing"
schedule: "0 8 * * *"
timezone: "America/New_York"
enabled: true
missed_strategy: "run_immediately"
last_run: "2026-02-03T08:00:15"
next_run: "2026-02-04T08:00:00"
last_result: "success"
---

## Scheduled Task: Daily Briefing

**Schedule**: Every day at 8:00 AM
**Timezone**: America/New_York
**Status**: Enabled
**Missed Strategy**: Run immediately if missed

### Action

Generate a daily briefing with:
- Pending approval requests count
- New action items since yesterday
- Active plans status
- Watcher health status

```yaml
action:
  type: "generate_briefing"
  template: "daily"
  output_path: "/Briefings/briefing_{{date}}.md"
  include:
    - pending_approvals
    - new_action_items
    - active_plans
    - watcher_status
```

### Execution History

| Date | Time | Duration | Result |
|------|------|----------|--------|
| 2026-02-03 | 08:00:15 | 2.3s | ✅ Success |
| 2026-02-02 | 08:00:12 | 2.1s | ✅ Success |
| 2026-02-01 | 08:05:00 | 2.5s | ⚠️ Delayed (system was offline) |
```

## Action Types

```python
# Supported action types for scheduled tasks
ACTION_TYPES = {
    "generate_briefing": {
        "template": str,  # "daily" | "weekly"
        "output_path": str,
        "include": list[str],
    },
    "generate_audit": {
        "period": str,  # "week" | "month"
        "output_path": str,
        "metrics": list[str],
    },
    "check_approvals": {
        # No additional params - checks expired approvals
    },
    "update_dashboard": {
        # No additional params - refreshes dashboard
    },
    "fetch_engagement": {
        "platform": str,  # "linkedin"
        "posts_count": int,  # How many recent posts
    },
    "custom": {
        "script": str,  # Path to Python script
        "args": dict,
    },
}
```

## Default Task Configurations

```python
DEFAULT_TASKS = [
    {
        "id": "schedule_daily_briefing",
        "name": "Daily Briefing",
        "schedule": "0 8 * * *",  # 8:00 AM daily
        "action": {
            "type": "generate_briefing",
            "template": "daily",
            "output_path": "/Briefings/briefing_{{date}}.md",
        },
        "missed_strategy": "run_immediately",
    },
    {
        "id": "schedule_weekly_audit",
        "name": "Weekly Audit",
        "schedule": "0 21 * * 0",  # Sunday 9:00 PM
        "action": {
            "type": "generate_audit",
            "period": "week",
            "output_path": "/Briefings/audit_week_{{week}}.md",
        },
        "missed_strategy": "skip",  # Don't run old audits
    },
    {
        "id": "schedule_approval_check",
        "name": "Approval Expiration Check",
        "schedule": "0 * * * *",  # Every hour
        "action": {
            "type": "check_approvals",
        },
        "missed_strategy": "skip",
    },
    {
        "id": "schedule_dashboard_update",
        "name": "Dashboard Update",
        "schedule": "*/15 * * * *",  # Every 15 minutes
        "action": {
            "type": "update_dashboard",
        },
        "missed_strategy": "skip",
    },
]
```

## Error Handling

```python
class SchedulerError(Exception):
    """Base exception for scheduler service."""

class TaskNotFoundError(SchedulerError):
    """Raised when task ID not found."""

class InvalidCronError(SchedulerError):
    """Raised when cron expression is invalid."""

class TaskExecutionError(SchedulerError):
    """Raised when task execution fails."""

class SchedulerNotRunningError(SchedulerError):
    """Raised when scheduler is not started."""
```

## Events & Logging

| Event | Log Level | Details |
|-------|-----------|---------|
| Scheduler started | INFO | tasks_loaded |
| Scheduler stopped | INFO | - |
| Task created | INFO | task_id, schedule |
| Task updated | INFO | task_id, changes |
| Task deleted | INFO | task_id |
| Task enabled | INFO | task_id |
| Task disabled | INFO | task_id |
| Task execution started | INFO | task_id |
| Task execution succeeded | INFO | task_id, duration_ms |
| Task execution failed | ERROR | task_id, error |
| Missed schedule detected | WARNING | task_id, missed_time |
| Missed schedule handled | INFO | task_id, strategy, action_taken |
