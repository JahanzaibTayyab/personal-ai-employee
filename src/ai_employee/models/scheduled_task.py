"""ScheduledTask model - recurring or one-time scheduled operations."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MissedStrategy(str, Enum):
    """How to handle missed schedules (FR-029)."""

    SKIP = "skip"
    RUN_IMMEDIATELY = "run_immediately"
    QUEUE = "queue"


class TaskType(str, Enum):
    """Type of scheduled task action."""

    BRIEFING = "briefing"
    AUDIT = "audit"
    UPDATE_DASHBOARD = "update_dashboard"
    CHECK_APPROVALS = "check_approvals"
    CUSTOM = "custom"


# Regex for validating cron expressions (5-field format)
CRON_REGEX = re.compile(
    r"^(\*|[0-9]|[1-5][0-9]|(\*|[0-9]|[1-5][0-9])(,(\*|[0-9]|[1-5][0-9]))*|"
    r"([0-9]|[1-5][0-9])-([0-9]|[1-5][0-9])|\*/[0-9]+)\s+"  # minute
    r"(\*|[0-9]|1[0-9]|2[0-3]|(\*|[0-9]|1[0-9]|2[0-3])(,(\*|[0-9]|1[0-9]|2[0-3]))*|"
    r"([0-9]|1[0-9]|2[0-3])-([0-9]|1[0-9]|2[0-3])|\*/[0-9]+)\s+"  # hour
    r"(\*|[1-9]|[12][0-9]|3[01]|(\*|[1-9]|[12][0-9]|3[01])(,(\*|[1-9]|[12][0-9]|3[01]))*|"
    r"([1-9]|[12][0-9]|3[01])-([1-9]|[12][0-9]|3[01])|\*/[0-9]+)\s+"  # day of month
    r"(\*|[1-9]|1[0-2]|(\*|[1-9]|1[0-2])(,(\*|[1-9]|1[0-2]))*|"
    r"([1-9]|1[0-2])-([1-9]|1[0-2])|\*/[0-9]+)\s+"  # month
    r"(\*|[0-6]|(\*|[0-6])(,(\*|[0-6]))*|[0-6]-[0-6]|\*/[0-9]+)$"  # day of week
)


@dataclass
class ScheduledTask:
    """Scheduled recurring or one-time task (FR-026 to FR-030).

    Stored as markdown files in /Schedules/ folder with YAML frontmatter.

    Schedule can be:
    - Cron expression (5-field): "0 8 * * *" = Daily at 8:00 AM
    - ISO datetime for one-time: "2026-02-10T15:00:00"
    """

    id: str
    name: str
    schedule: str  # Cron expression or ISO datetime
    action: dict[str, Any]  # Action configuration
    enabled: bool = True
    timezone: str = "local"  # User's timezone (FR-030)
    last_run: datetime | None = None
    next_run: datetime | None = None
    missed_strategy: MissedStrategy = MissedStrategy.RUN_IMMEDIATELY
    last_result: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        name: str,
        schedule: str,
        task_type: TaskType,
        action_config: dict[str, Any] | None = None,
        timezone: str = "local",
        missed_strategy: MissedStrategy = MissedStrategy.RUN_IMMEDIATELY,
    ) -> "ScheduledTask":
        """Create a new scheduled task.

        Args:
            name: Human-readable name for the task
            schedule: Cron expression or ISO datetime string
            task_type: Type of action to perform
            action_config: Additional action configuration
            timezone: Timezone for schedule interpretation
            missed_strategy: How to handle missed executions

        Returns:
            New ScheduledTask instance
        """
        now = datetime.now()
        task_id = f"schedule_{name.lower().replace(' ', '_')}"

        action = {
            "type": task_type.value,
            **(action_config or {}),
        }

        return cls(
            id=task_id,
            name=name,
            schedule=schedule,
            action=action,
            timezone=timezone,
            missed_strategy=missed_strategy,
            created_at=now,
        )

    def is_cron(self) -> bool:
        """Check if schedule is a cron expression (recurring)."""
        return " " in self.schedule

    def is_one_time(self) -> bool:
        """Check if schedule is a one-time datetime."""
        return not self.is_cron()

    def get_one_time_datetime(self) -> datetime | None:
        """Get the datetime for one-time schedules."""
        if self.is_one_time():
            try:
                return datetime.fromisoformat(self.schedule)
            except ValueError:
                return None
        return None

    def to_frontmatter(self) -> dict[str, Any]:
        """Convert task to YAML frontmatter dictionary."""
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "schedule": self.schedule,
            "action": self.action,
            "enabled": self.enabled,
            "timezone": self.timezone,
            "missed_strategy": self.missed_strategy.value,
            "created_at": self.created_at.isoformat(),
        }

        if self.last_run:
            data["last_run"] = self.last_run.isoformat()
        if self.next_run:
            data["next_run"] = self.next_run.isoformat()
        if self.last_result:
            data["last_result"] = self.last_result
        if self.error:
            data["error"] = self.error

        return data

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any]) -> "ScheduledTask":
        """Create ScheduledTask from YAML frontmatter dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            schedule=data["schedule"],
            action=data.get("action", {}),
            enabled=data.get("enabled", True),
            timezone=data.get("timezone", "local"),
            last_run=(
                datetime.fromisoformat(data["last_run"])
                if data.get("last_run")
                else None
            ),
            next_run=(
                datetime.fromisoformat(data["next_run"])
                if data.get("next_run")
                else None
            ),
            missed_strategy=MissedStrategy(data.get("missed_strategy", "run_immediately")),
            last_result=data.get("last_result"),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    def get_filename(self) -> str:
        """Generate filename for this scheduled task."""
        return f"{self.id}.md"

    def __post_init__(self) -> None:
        """Validate the scheduled task."""
        # Validate schedule format
        if self.is_cron():
            if not self._is_valid_cron(self.schedule):
                raise ValueError(f"Invalid cron expression: {self.schedule}")
        else:
            try:
                datetime.fromisoformat(self.schedule)
            except ValueError as e:
                raise ValueError(f"Invalid datetime format: {self.schedule}") from e

    @staticmethod
    def _is_valid_cron(expression: str) -> bool:
        """Validate a cron expression (simplified validation)."""
        parts = expression.split()
        if len(parts) != 5:
            return False

        # Basic validation: each part should be *, a number, range, or step
        for part in parts:
            if not re.match(r"^(\*|\d+(-\d+)?)(,(\*|\d+(-\d+)?))*(/\d+)?$", part):
                return False
        return True


# Predefined task templates
def create_daily_briefing_task(
    hour: int = 8,
    minute: int = 0,
    timezone: str = "local",
) -> ScheduledTask:
    """Create a daily briefing task template.

    Args:
        hour: Hour to run (0-23)
        minute: Minute to run (0-59)
        timezone: Timezone for schedule

    Returns:
        Configured ScheduledTask for daily briefing
    """
    return ScheduledTask.create(
        name="Daily Briefing",
        schedule=f"{minute} {hour} * * *",
        task_type=TaskType.BRIEFING,
        action_config={
            "include_pending_approvals": True,
            "include_action_items": True,
            "include_active_plans": True,
            "include_yesterday_completed": True,
        },
        timezone=timezone,
    )


def create_weekly_audit_task(
    day_of_week: int = 0,  # 0 = Sunday
    hour: int = 21,
    minute: int = 0,
    timezone: str = "local",
) -> ScheduledTask:
    """Create a weekly audit task template.

    Args:
        day_of_week: Day to run (0=Sunday, 6=Saturday)
        hour: Hour to run (0-23)
        minute: Minute to run (0-59)
        timezone: Timezone for schedule

    Returns:
        Configured ScheduledTask for weekly audit
    """
    return ScheduledTask.create(
        name="Weekly Audit",
        schedule=f"{minute} {hour} * * {day_of_week}",
        task_type=TaskType.AUDIT,
        action_config={
            "analyze_completed_items": True,
            "analyze_processing_times": True,
            "analyze_approval_rates": True,
            "generate_recommendations": True,
        },
        timezone=timezone,
    )
