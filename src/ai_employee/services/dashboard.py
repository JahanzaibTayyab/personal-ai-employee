"""Dashboard service - updates Dashboard.md with current status."""

from datetime import datetime, timedelta

from ai_employee.config import VaultConfig
from ai_employee.models.activity_log import ActivityLogEntry, Outcome
from ai_employee.models.dashboard import DashboardState
from ai_employee.utils.jsonl_logger import JsonlLogger


class DashboardService:
    """Service for generating and updating Dashboard.md."""

    ERROR_THRESHOLD = 5  # errors per hour to trigger warning

    def __init__(self, vault_config: VaultConfig):
        """Initialize the dashboard service.

        Args:
            vault_config: Vault configuration with paths
        """
        self.vault_config = vault_config
        self.activity_logger = JsonlLogger[ActivityLogEntry](
            logs_dir=vault_config.logs,
            prefix="claude",
            serializer=lambda e: e.to_json(),
            deserializer=ActivityLogEntry.from_json,
        )

    def get_pending_count(self) -> int:
        """Count pending items in /Needs_Action folder.

        Returns:
            Number of .md files in Needs_Action folder
        """
        needs_action = self.vault_config.needs_action
        if not needs_action.exists():
            return 0

        count = 0
        for item in needs_action.rglob("*.md"):
            if item.is_file():
                count += 1
        return count

    def get_recent_activity(self, count: int = 10) -> list[ActivityLogEntry]:
        """Get recent activity from logs.

        Args:
            count: Number of entries to retrieve

        Returns:
            List of recent activity entries (newest first)
        """
        return self.activity_logger.read_recent(count)

    def get_processed_today(self) -> int:
        """Count items processed today.

        Returns:
            Number of successful process actions today
        """
        entries = self.activity_logger.read_entries()
        return sum(1 for e in entries if e.outcome == Outcome.SUCCESS)

    def get_error_count_hour(self) -> int:
        """Count errors in the last hour.

        Returns:
            Number of error entries in the last hour
        """
        entries = self.activity_logger.read_entries()
        one_hour_ago = datetime.now() - timedelta(hours=1)

        return sum(
            1 for e in entries
            if e.outcome == Outcome.FAILURE and e.timestamp > one_hour_ago
        )

    def get_watcher_status(self) -> str:
        """Check if watcher is running.

        Returns:
            'running', 'stopped', or 'unknown'
        """
        # Check for recent watcher events (within last 2 minutes)
        watcher_logger = JsonlLogger[dict](
            logs_dir=self.vault_config.logs,
            prefix="watcher",
            serializer=lambda e: str(e),
            deserializer=lambda s: {},
        )

        try:
            log_path = watcher_logger._get_log_path()
            if not log_path.exists():
                return "stopped"

            # Check if log file was modified recently
            mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
            if datetime.now() - mtime < timedelta(minutes=2):
                return "running"
            return "stopped"
        except Exception:
            return "unknown"

    def generate_warnings(self, error_count_hour: int) -> list[str]:
        """Generate warning messages based on system state.

        Args:
            error_count_hour: Number of errors in the last hour

        Returns:
            List of warning messages
        """
        warnings = []

        if error_count_hour >= self.ERROR_THRESHOLD:
            warnings.append(
                f"High error rate: {error_count_hour} errors in the last hour"
            )

        return warnings

    def generate_state(self) -> DashboardState:
        """Generate current dashboard state.

        Returns:
            DashboardState with all current metrics
        """
        error_count_hour = self.get_error_count_hour()

        return DashboardState(
            last_updated=datetime.now(),
            watcher_status=self.get_watcher_status(),
            pending_count=self.get_pending_count(),
            processed_today=self.get_processed_today(),
            recent_activity=self.get_recent_activity(),
            warnings=self.generate_warnings(error_count_hour),
            error_count_hour=error_count_hour,
        )

    def update_dashboard(self) -> None:
        """Update Dashboard.md with current state."""
        state = self.generate_state()
        content = state.to_markdown()

        self.vault_config.dashboard.write_text(content)

    def read_dashboard(self) -> str | None:
        """Read current Dashboard.md content.

        Returns:
            Dashboard content or None if not found
        """
        if self.vault_config.dashboard.exists():
            return self.vault_config.dashboard.read_text()
        return None
