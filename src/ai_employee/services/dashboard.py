"""Dashboard service - updates Dashboard.md with current status."""

from datetime import datetime, timedelta

from ai_employee.config import VaultConfig
from ai_employee.models.activity_log import ActivityLogEntry, Outcome
from ai_employee.models.dashboard import DashboardState
from ai_employee.utils.jsonl_logger import JsonlLogger


class DashboardService:
    """Service for generating and updating Dashboard.md."""

    ERROR_THRESHOLD = 5  # errors per hour to trigger warning
    STALE_THRESHOLD_HOURS = 4  # hours before expiry to consider "stale"

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
        self._approval_service = None
        self._planner_service = None

    def _get_approval_service(self) -> "ApprovalService":
        """Lazy load ApprovalService to avoid circular imports."""
        if self._approval_service is None:
            from ai_employee.services.approval import ApprovalService
            self._approval_service = ApprovalService(self.vault_config)
        return self._approval_service

    def _get_planner_service(self) -> "PlannerService":
        """Lazy load PlannerService to avoid circular imports."""
        if self._planner_service is None:
            from ai_employee.services.planner import PlannerService
            self._planner_service = PlannerService(self.vault_config)
        return self._planner_service

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

    def get_pending_approvals_count(self) -> int:
        """Count pending approval requests.

        Returns:
            Number of pending approvals in /Pending_Approval/
        """
        try:
            service = self._get_approval_service()
            return len(service.get_pending_requests())
        except Exception:
            return 0

    def get_stale_approvals_count(self) -> int:
        """Count stale approvals (expiring within threshold).

        Returns:
            Number of approvals expiring within STALE_THRESHOLD_HOURS
        """
        try:
            service = self._get_approval_service()
            pending = service.get_pending_requests()
            stale_threshold = timedelta(hours=self.STALE_THRESHOLD_HOURS)

            return sum(
                1 for r in pending
                if r.time_remaining() < stale_threshold
            )
        except Exception:
            return 0

    def get_approval_watcher_status(self) -> str:
        """Check if approval watcher is running.

        Returns:
            'running', 'stopped', or 'unknown'
        """
        # Check for recent approval watcher events
        try:
            watcher_logger = JsonlLogger[dict](
                logs_dir=self.vault_config.logs,
                prefix="watcher",
                serializer=lambda e: str(e),
                deserializer=lambda s: {},
            )
            log_path = watcher_logger._get_log_path()
            if not log_path.exists():
                return "stopped"

            # Check log content for approval watcher entries
            content = log_path.read_text()
            if '"source_type": "approval"' in content:
                mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
                if datetime.now() - mtime < timedelta(minutes=2):
                    return "running"
            return "stopped"
        except Exception:
            return "unknown"

    def get_whatsapp_watcher_status(self) -> str:
        """Check WhatsApp watcher status.

        Returns:
            'connected', 'disconnected', 'qr_required', 'session_expired', or 'unknown'
        """
        try:
            watcher_logger = JsonlLogger[dict](
                logs_dir=self.vault_config.logs,
                prefix="watcher",
                serializer=lambda e: str(e),
                deserializer=lambda s: {},
            )
            log_path = watcher_logger._get_log_path()
            if not log_path.exists():
                return "disconnected"

            # Check log content for whatsapp watcher entries
            content = log_path.read_text()
            if '"source_type": "whatsapp"' in content:
                # Check for most recent status
                import re
                status_matches = re.findall(
                    r'"new_status":\s*"(\w+)"',
                    content
                )
                if status_matches:
                    return str(status_matches[-1])

                mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
                if datetime.now() - mtime < timedelta(minutes=2):
                    return "connected"
            return "disconnected"
        except Exception:
            return "unknown"

    def get_active_plan_count(self) -> int:
        """Count active plans.

        Returns:
            Number of active (non-completed) plans
        """
        try:
            service = self._get_planner_service()
            return len(service.get_active_plans())
        except Exception:
            return 0

    def get_active_plan_info(self) -> tuple[str | None, str | None]:
        """Get info about current active plan.

        Returns:
            Tuple of (plan_name, progress_string) or (None, None)
        """
        try:
            service = self._get_planner_service()
            active = service.get_active_plans()
            if active:
                # Get most recent active plan
                plan = active[0]
                completed, total = plan.get_progress()
                return plan.objective[:50], f"{completed}/{total} steps"
            return None, None
        except Exception:
            return None, None

    def get_whatsapp_messages_today(self) -> int:
        """Count WhatsApp messages detected today.

        Returns:
            Number of WhatsApp action files created today
        """
        try:
            whatsapp_folder = self.vault_config.needs_action_whatsapp
            if not whatsapp_folder.exists():
                return 0

            today = datetime.now().date()
            count = 0
            for file in whatsapp_folder.glob("WHATSAPP_*.md"):
                # Check file creation date
                mtime = datetime.fromtimestamp(file.stat().st_mtime).date()
                if mtime == today:
                    count += 1
            return count
        except Exception:
            return 0

    def generate_warnings(
        self,
        error_count_hour: int,
        stale_approvals: int = 0,
        whatsapp_status: str = "disconnected",
    ) -> list[str]:
        """Generate warning messages based on system state.

        Args:
            error_count_hour: Number of errors in the last hour
            stale_approvals: Number of stale approval requests
            whatsapp_status: Current WhatsApp watcher status

        Returns:
            List of warning messages
        """
        warnings = []

        if error_count_hour >= self.ERROR_THRESHOLD:
            warnings.append(
                f"High error rate: {error_count_hour} errors in the last hour"
            )

        if stale_approvals > 0:
            warnings.append(
                f"Stale approvals: {stale_approvals} request(s) expiring within "
                f"{self.STALE_THRESHOLD_HOURS} hours"
            )

        if whatsapp_status == "session_expired":
            warnings.append(
                "WhatsApp session expired - please re-authenticate"
            )
        elif whatsapp_status == "error":
            warnings.append(
                "WhatsApp watcher error - check logs for details"
            )

        return warnings

    def generate_state(self) -> DashboardState:
        """Generate current dashboard state.

        Returns:
            DashboardState with all current metrics
        """
        error_count_hour = self.get_error_count_hour()
        stale_approvals = self.get_stale_approvals_count()
        whatsapp_status = self.get_whatsapp_watcher_status()
        plan_name, plan_progress = self.get_active_plan_info()

        return DashboardState(
            last_updated=datetime.now(),
            watcher_status=self.get_watcher_status(),
            pending_count=self.get_pending_count(),
            processed_today=self.get_processed_today(),
            recent_activity=self.get_recent_activity(),
            warnings=self.generate_warnings(error_count_hour, stale_approvals, whatsapp_status),
            error_count_hour=error_count_hour,
            # Silver tier: Approval metrics
            pending_approvals_count=self.get_pending_approvals_count(),
            stale_approvals_count=stale_approvals,
            approval_watcher_status=self.get_approval_watcher_status(),
            # Silver tier: WhatsApp metrics
            whatsapp_watcher_status=whatsapp_status,
            whatsapp_messages_today=self.get_whatsapp_messages_today(),
            # Silver tier: Plan metrics
            active_plan_count=self.get_active_plan_count(),
            active_plan_name=plan_name,
            active_plan_progress=plan_progress,
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
