"""Audit logging service for tracking all AI Employee actions.

Provides comprehensive audit trail with JSONL storage, querying,
retention management, and archival capabilities.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.utils.redaction import redact_dict


class AuditService:
    """Service for logging and querying audit entries.

    Stores audit entries as JSONL files in the vault's Logs directory
    with date-based file naming: audit_YYYY-MM-DD.log
    """

    def __init__(self, vault_config: VaultConfig) -> None:
        """Initialize AuditService.

        Args:
            vault_config: Vault configuration with paths.
        """
        self._vault_config = vault_config
        self._logs_dir = vault_config.logs
        self._archive_dir = vault_config.logs / "archive"

    def _get_log_path(self, date: datetime | None = None) -> Path:
        """Get the log file path for a given date.

        Args:
            date: Date for the log file. Defaults to today.

        Returns:
            Path to the audit log file.
        """
        if date is None:
            date = datetime.now()
        filename = f"audit_{date.strftime('%Y-%m-%d')}.log"
        return self._logs_dir / filename

    def log_action(
        self,
        action_type: str,
        actor: str,
        target: str,
        parameters: dict[str, Any] | None = None,
        result: str = "success",
        error_message: str | None = None,
        correlation_id: str | None = None,
        duration_ms: int | None = None,
        approval_status: str = "not_required",
        approved_by: str | None = None,
    ) -> dict[str, Any]:
        """Log an audit entry.

        Args:
            action_type: Type of action performed.
            actor: Who or what performed the action.
            target: What the action was performed on.
            parameters: Optional parameters for the action.
            result: Result of the action (success/failure/pending).
            error_message: Optional error message if action failed.
            correlation_id: Optional ID to correlate related entries.
            duration_ms: Optional duration of the action in milliseconds.
            approval_status: Approval status (not_required/pending/approved/rejected).
            approved_by: Who approved the action, if applicable.

        Returns:
            The audit entry dictionary that was logged.
        """
        self._logs_dir.mkdir(parents=True, exist_ok=True)

        entry: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": actor,
            "target": target,
            "result": result,
            "approval_status": approval_status,
        }

        if parameters is not None:
            entry["parameters"] = redact_dict(parameters)
        if error_message is not None:
            entry["error_message"] = error_message
        if correlation_id is not None:
            entry["correlation_id"] = correlation_id
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        if approved_by is not None:
            entry["approved_by"] = approved_by

        log_path = self._get_log_path()
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return entry

    def read_entries(self, date: datetime | None = None) -> list[dict[str, Any]]:
        """Read all audit entries for a given date.

        Args:
            date: Date to read entries for. Defaults to today.

        Returns:
            List of audit entry dictionaries.
        """
        log_path = self._get_log_path(date)

        if not log_path.exists():
            return []

        entries: list[dict[str, Any]] = []
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return entries

    def query_entries(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        action_type: str | None = None,
        actor: str | None = None,
        target: str | None = None,
        result: str | None = None,
        correlation_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query audit entries with filters.

        Args:
            start_date: Start of date range (inclusive). Defaults to today.
            end_date: End of date range (inclusive). Defaults to today.
            action_type: Filter by action type.
            actor: Filter by actor.
            target: Filter by target (substring match).
            result: Filter by result.
            correlation_id: Filter by correlation ID.
            limit: Maximum number of entries to return.

        Returns:
            List of matching audit entry dictionaries.
        """
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if end_date is None:
            end_date = datetime.now()

        all_entries: list[dict[str, Any]] = []
        current_date = start_date
        while current_date <= end_date:
            all_entries.extend(self.read_entries(current_date))
            current_date = current_date + timedelta(days=1)

        filtered: list[dict[str, Any]] = []
        for entry in all_entries:
            if action_type and entry.get("action_type") != action_type:
                continue
            if actor and entry.get("actor") != actor:
                continue
            if target and target not in entry.get("target", ""):
                continue
            if result and entry.get("result") != result:
                continue
            if correlation_id and entry.get("correlation_id") != correlation_id:
                continue
            filtered.append(entry)
            if len(filtered) >= limit:
                break

        return filtered

    def get_action_counts(
        self,
        date: datetime | None = None,
    ) -> dict[str, int]:
        """Get counts of each action type for a given date.

        Args:
            date: Date to count actions for. Defaults to today.

        Returns:
            Dictionary mapping action types to their counts.
        """
        entries = self.read_entries(date)
        counts: dict[str, int] = {}
        for entry in entries:
            action_type = entry.get("action_type", "unknown")
            counts[action_type] = counts.get(action_type, 0) + 1
        return counts

    def get_retention_stats(self) -> dict[str, Any]:
        """Get statistics about audit log retention.

        Returns:
            Dictionary with log file count, date range, and total size.
        """
        if not self._logs_dir.exists():
            return {
                "file_count": 0,
                "oldest_date": None,
                "newest_date": None,
                "total_size_bytes": 0,
            }

        log_files = sorted(self._logs_dir.glob("audit_*.log"))
        if not log_files:
            return {
                "file_count": 0,
                "oldest_date": None,
                "newest_date": None,
                "total_size_bytes": 0,
            }

        dates: list[str] = []
        total_size = 0
        for log_file in log_files:
            try:
                date_str = log_file.stem.replace("audit_", "")
                datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date_str)
                total_size += log_file.stat().st_size
            except (ValueError, OSError):
                continue

        return {
            "file_count": len(dates),
            "oldest_date": min(dates) if dates else None,
            "newest_date": max(dates) if dates else None,
            "total_size_bytes": total_size,
        }

    def archive_old_entries(
        self,
        retention_days: int = 30,
    ) -> list[str]:
        """Archive audit log files older than retention period.

        Moves old log files to the archive subdirectory.

        Args:
            retention_days: Number of days to retain logs before archiving.

        Returns:
            List of archived file names.
        """
        if not self._logs_dir.exists():
            return []

        self._archive_dir.mkdir(parents=True, exist_ok=True)
        cutoff = datetime.now() - timedelta(days=retention_days)
        archived: list[str] = []

        for log_file in self._logs_dir.glob("audit_*.log"):
            try:
                date_str = log_file.stem.replace("audit_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    dest = self._archive_dir / log_file.name
                    log_file.rename(dest)
                    archived.append(log_file.name)
            except (ValueError, OSError):
                continue

        return archived

    def purge_archived(
        self,
        older_than_days: int = 90,
    ) -> list[str]:
        """Permanently delete archived logs older than specified days.

        Args:
            older_than_days: Delete archived files older than this many days.

        Returns:
            List of deleted file names.
        """
        if not self._archive_dir.exists():
            return []

        cutoff = datetime.now() - timedelta(days=older_than_days)
        purged: list[str] = []

        for log_file in self._archive_dir.glob("audit_*.log"):
            try:
                date_str = log_file.stem.replace("audit_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    log_file.unlink()
                    purged.append(log_file.name)
            except (ValueError, OSError):
                continue

        return purged
