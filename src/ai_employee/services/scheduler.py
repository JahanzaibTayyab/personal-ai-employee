"""Scheduler service - manage scheduled tasks with cron-based scheduling.

Supports recurring and one-time scheduled tasks with timezone support.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.models.scheduled_task import (
    ScheduledTask,
    TaskType,
    MissedStrategy,
)
from ai_employee.utils.frontmatter import parse_frontmatter, generate_frontmatter
from ai_employee.utils.jsonl_logger import JsonlLogger


class SchedulerService:
    """Service for managing scheduled tasks.

    Features:
    - Add, remove, and update scheduled tasks
    - Support for cron expressions and one-time datetimes
    - Timezone support
    - Missed schedule handling (skip, run_immediately, queue)
    - Execution logging
    """

    def __init__(self, vault_config: VaultConfig):
        """Initialize the scheduler service.

        Args:
            vault_config: Vault configuration with paths
        """
        self._config = vault_config
        self._logger = JsonlLogger[dict](
            logs_dir=vault_config.logs,
            prefix="scheduler",
            serializer=lambda e: str(e),
            deserializer=lambda s: {},
        )

    def _log_operation(
        self,
        operation: str,
        success: bool,
        details: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Log a scheduler operation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "success": success,
            **(details or {}),
        }
        if error:
            entry["error"] = error
        self._logger.log(entry)

    def _get_task_path(self, task_id: str) -> Path:
        """Get the file path for a task."""
        return self._config.schedules / f"{task_id}.md"

    def _save_task(self, task: ScheduledTask) -> None:
        """Save a task to disk."""
        self._config.schedules.mkdir(parents=True, exist_ok=True)

        frontmatter = task.to_frontmatter()
        content = generate_frontmatter(frontmatter)

        # Add task description body
        content += f"\n# Scheduled Task: {task.name}\n\n"
        content += f"**Schedule**: `{task.schedule}`\n"
        content += f"**Type**: {task.action.get('type', 'custom')}\n"
        content += f"**Enabled**: {'Yes' if task.enabled else 'No'}\n"
        content += f"**Timezone**: {task.timezone}\n"

        if task.last_run:
            content += f"\n**Last Run**: {task.last_run.strftime('%Y-%m-%d %H:%M')}\n"
        if task.next_run:
            content += f"**Next Run**: {task.next_run.strftime('%Y-%m-%d %H:%M')}\n"

        content += f"\n## Action Configuration\n\n"
        for key, value in task.action.items():
            content += f"- **{key}**: {value}\n"

        file_path = self._get_task_path(task.id)
        file_path.write_text(content)

    def _load_task(self, task_id: str) -> ScheduledTask | None:
        """Load a task from disk."""
        file_path = self._get_task_path(task_id)
        if not file_path.exists():
            return None

        content = file_path.read_text()
        frontmatter, _ = parse_frontmatter(content)

        try:
            return ScheduledTask.from_frontmatter(frontmatter)
        except (KeyError, ValueError):
            return None

    def add_task(self, task: ScheduledTask) -> bool:
        """Add or update a scheduled task.

        Args:
            task: Task to add

        Returns:
            True if successful
        """
        try:
            self._save_task(task)
            self._log_operation("add_task", True, {
                "task_id": task.id,
                "task_name": task.name,
                "schedule": task.schedule,
            })
            return True
        except Exception as e:
            self._log_operation("add_task", False, error=str(e))
            return False

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task.

        Args:
            task_id: ID of task to remove

        Returns:
            True if removed, False if not found
        """
        file_path = self._get_task_path(task_id)
        if not file_path.exists():
            return False

        file_path.unlink()
        self._log_operation("remove_task", True, {"task_id": task_id})
        return True

    def get_task(self, task_id: str) -> ScheduledTask | None:
        """Get a task by ID.

        Args:
            task_id: ID of task to get

        Returns:
            ScheduledTask if found, None otherwise
        """
        return self._load_task(task_id)

    def get_all_tasks(self) -> list[ScheduledTask]:
        """Get all scheduled tasks.

        Returns:
            List of all scheduled tasks
        """
        tasks: list[ScheduledTask] = []
        schedules_dir = self._config.schedules

        if not schedules_dir.exists():
            return tasks

        for file_path in schedules_dir.glob("*.md"):
            task_id = file_path.stem
            task = self._load_task(task_id)
            if task:
                tasks.append(task)

        return tasks

    def enable_task(self, task_id: str) -> bool:
        """Enable a task.

        Args:
            task_id: ID of task to enable

        Returns:
            True if successful, False if not found
        """
        task = self._load_task(task_id)
        if not task:
            return False

        task.enabled = True
        self._save_task(task)
        self._log_operation("enable_task", True, {"task_id": task_id})
        return True

    def disable_task(self, task_id: str) -> bool:
        """Disable a task.

        Args:
            task_id: ID of task to disable

        Returns:
            True if successful, False if not found
        """
        task = self._load_task(task_id)
        if not task:
            return False

        task.enabled = False
        self._save_task(task)
        self._log_operation("disable_task", True, {"task_id": task_id})
        return True

    def run_task(self, task_id: str) -> dict[str, Any]:
        """Run a task immediately.

        Args:
            task_id: ID of task to run

        Returns:
            Dict with success status and result/error
        """
        task = self._load_task(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}

        if not task.enabled:
            return {"success": False, "error": "Task is disabled"}

        try:
            result = self._execute_action(task)

            # Update task status
            task.last_run = datetime.now()
            task.last_result = "success" if result.get("success") else "failed"
            task.error = result.get("error")
            self._save_task(task)

            self._log_operation("run_task", result.get("success", False), {
                "task_id": task_id,
                "task_type": task.action.get("type"),
                "result": result,
            })

            return result

        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            task.last_run = datetime.now()
            task.last_result = "failed"
            task.error = str(e)
            self._save_task(task)

            self._log_operation("run_task", False, {
                "task_id": task_id,
            }, error=str(e))

            return error_result

    def _execute_action(self, task: ScheduledTask) -> dict[str, Any]:
        """Execute a task's action.

        Args:
            task: Task to execute

        Returns:
            Dict with execution result
        """
        task_type = task.action.get("type", "custom")

        if task_type == TaskType.BRIEFING.value:
            return self._execute_briefing(task)
        elif task_type == TaskType.AUDIT.value:
            return self._execute_audit(task)
        elif task_type == TaskType.UPDATE_DASHBOARD.value:
            return self._execute_update_dashboard(task)
        elif task_type == TaskType.CHECK_APPROVALS.value:
            return self._execute_check_approvals(task)
        elif task_type == TaskType.CUSTOM.value:
            return self._execute_custom(task)
        else:
            return {"success": False, "error": f"Unknown task type: {task_type}"}

    def _execute_briefing(self, task: ScheduledTask) -> dict[str, Any]:
        """Execute a briefing generation task."""
        try:
            content = self._generate_briefing(task.action)

            # Save briefing to Briefings folder
            self._config.briefings.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            briefing_file = self._config.briefings / f"briefing_{timestamp}.md"
            briefing_file.write_text(content)

            return {
                "success": True,
                "message": "Briefing generated",
                "file": str(briefing_file),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_briefing(self, config: dict[str, Any]) -> str:
        """Generate a daily briefing.

        Args:
            config: Briefing configuration

        Returns:
            Briefing content
        """
        now = datetime.now()
        content = f"# Daily Briefing - {now.strftime('%Y-%m-%d')}\n\n"
        content += f"Generated at: {now.strftime('%H:%M')}\n\n"

        if config.get("include_pending_approvals"):
            pending_count = len(list(self._config.pending_approval.glob("*.md")))
            content += f"## Pending Approvals\n\n"
            content += f"{pending_count} items awaiting approval\n\n"

        if config.get("include_action_items"):
            action_count = len(list(self._config.needs_action.glob("**/*.md")))
            content += f"## Action Items\n\n"
            content += f"{action_count} items needing action\n\n"

        if config.get("include_active_plans"):
            plans_count = len(list(self._config.plans.glob("*.md")))
            content += f"## Active Plans\n\n"
            content += f"{plans_count} active plans\n\n"

        return content

    def _execute_audit(self, task: ScheduledTask) -> dict[str, Any]:
        """Execute a weekly audit task."""
        try:
            result = self._generate_audit(task.action)
            return {"success": True, "audit": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_audit(self, config: dict[str, Any]) -> dict[str, Any]:
        """Generate audit data.

        Args:
            config: Audit configuration

        Returns:
            Audit results
        """
        result: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
        }

        if config.get("analyze_completed_items"):
            done_count = len(list(self._config.done.glob("*.md")))
            result["completed_items"] = done_count

        if config.get("analyze_approval_rates"):
            approved = len(list(self._config.approved.glob("*.md")))
            rejected = len(list(self._config.rejected.glob("*.md")))
            total = approved + rejected
            result["approval_rate"] = (approved / total * 100) if total > 0 else 0

        return result

    def _execute_update_dashboard(self, task: ScheduledTask) -> dict[str, Any]:
        """Execute a dashboard update task."""
        try:
            from ai_employee.services.dashboard import DashboardService

            dashboard = DashboardService(self._config)
            dashboard.update_dashboard()
            return {"success": True, "message": "Dashboard updated"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_check_approvals(self, task: ScheduledTask) -> dict[str, Any]:
        """Execute an approval check task."""
        try:
            from ai_employee.services.approval import ApprovalService

            approval = ApprovalService(self._config)
            expired = approval.check_expired_requests()
            expired_count = len(expired)
            return {
                "success": True,
                "expired_count": expired_count,
                "message": f"Found {expired_count} expired approvals",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_custom(self, task: ScheduledTask) -> dict[str, Any]:
        """Execute a custom task."""
        # Custom tasks need explicit handling
        # For now, just log and return success
        return {
            "success": True,
            "message": "Custom task executed (no-op)",
            "config": task.action,
        }

    def get_missed_tasks(self) -> list[ScheduledTask]:
        """Get tasks that missed their scheduled run.

        Returns:
            List of tasks with past next_run times
        """
        now = datetime.now()
        missed = []

        for task in self.get_all_tasks():
            if task.enabled and task.next_run and task.next_run < now:
                missed.append(task)

        return missed

    def handle_missed_task(self, task_id: str) -> dict[str, Any]:
        """Handle a missed task according to its strategy.

        Args:
            task_id: ID of missed task

        Returns:
            Dict with handling result
        """
        task = self._load_task(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}

        strategy = task.missed_strategy

        if strategy == MissedStrategy.SKIP:
            # Just update next_run and skip execution
            self._log_operation("handle_missed", True, {
                "task_id": task_id,
                "strategy": "skip",
            })
            return {"success": True, "action": "skipped"}

        elif strategy == MissedStrategy.RUN_IMMEDIATELY:
            # Execute the task now
            result = self.run_task(task_id)
            return {
                "success": result.get("success", False),
                "action": "run_immediately",
                "result": result,
            }

        elif strategy == MissedStrategy.QUEUE:
            # Queue for next opportunity (simplified: just run)
            result = self.run_task(task_id)
            return {
                "success": result.get("success", False),
                "action": "queued_and_run",
                "result": result,
            }

        return {"success": False, "error": f"Unknown strategy: {strategy}"}
