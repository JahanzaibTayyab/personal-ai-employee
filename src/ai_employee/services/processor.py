"""Item Processor service - processes items from /Needs_Action folder."""

import shutil
import time
from datetime import datetime
from pathlib import Path

from ai_employee.config import VaultConfig
from ai_employee.models.action_item import ActionItem, ActionItemStatus
from ai_employee.models.activity_log import ActionType, ActivityLogEntry, Outcome
from ai_employee.services.handbook import HandbookParser
from ai_employee.utils.frontmatter import generate_frontmatter, parse_frontmatter
from ai_employee.utils.jsonl_logger import JsonlLogger


class ItemProcessor:
    """Service for processing items in /Needs_Action folder."""

    def __init__(self, vault_config: VaultConfig):
        """Initialize the processor.

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
        self.handbook_parser = HandbookParser(vault_config.handbook)

    def get_pending_items(self) -> list[Path]:
        """Get all pending item files in /Needs_Action.

        Returns:
            List of paths to pending .md files, sorted by creation time (FIFO)
        """
        needs_action = self.vault_config.needs_action
        if not needs_action.exists():
            return []

        items = []
        for item in needs_action.rglob("*.md"):
            if item.is_file():
                items.append(item)

        # Sort by modification time (oldest first - FIFO)
        items.sort(key=lambda p: p.stat().st_mtime)
        return items

    def process_item(self, item_path: Path) -> bool:
        """Process a single action item.

        Args:
            item_path: Path to the action item .md file

        Returns:
            True if processing succeeded, False otherwise
        """
        start_time = time.time()
        item_id = item_path.name

        try:
            # Read the item
            content = item_path.read_text()
            frontmatter, body = parse_frontmatter(content)

            if not frontmatter:
                self._log_error(item_id, "Invalid frontmatter", start_time)
                return False

            # Parse action item
            action_item = ActionItem.from_frontmatter(frontmatter, body)

            # Apply handbook rules to detect priority
            detected_priority = self.handbook_parser.detect_priority(
                f"{action_item.original_name} {body}"
            )
            if detected_priority != action_item.priority:
                action_item.priority = detected_priority

            # Update status to processing
            action_item.status = ActionItemStatus.PROCESSING
            updated_content = generate_frontmatter(
                action_item.to_frontmatter(),
                body
            )
            item_path.write_text(updated_content)

            # Process based on type (for now, just mark as done)
            # Future: Apply handbook rules, take actions, etc.
            action_item.status = ActionItemStatus.DONE
            action_item.processed_at = datetime.now()

            # Move to Done folder
            done_path = self.vault_config.done / item_path.name
            final_content = generate_frontmatter(
                action_item.to_frontmatter(),
                body
            )

            # Ensure Done folder exists
            self.vault_config.done.mkdir(parents=True, exist_ok=True)

            # Write to Done and remove from Needs_Action
            done_path.write_text(final_content)
            item_path.unlink()

            # Log success
            duration_ms = int((time.time() - start_time) * 1000)
            self._log_success(item_id, "Processed and moved to Done", duration_ms)

            return True

        except Exception as e:
            self._log_error(item_id, str(e), start_time)
            self._quarantine_item(item_path, str(e))
            return False

    def _log_success(self, item_id: str, details: str, duration_ms: int) -> None:
        """Log a successful action.

        Args:
            item_id: ID of the processed item
            details: Details message
            duration_ms: Processing duration in milliseconds
        """
        entry = ActivityLogEntry(
            timestamp=datetime.now(),
            action_type=ActionType.PROCESS,
            item_id=item_id,
            outcome=Outcome.SUCCESS,
            duration_ms=duration_ms,
            details=details,
        )
        self.activity_logger.log(entry)

    def _log_error(self, item_id: str, error: str, start_time: float) -> None:
        """Log an error action.

        Args:
            item_id: ID of the item
            error: Error message
            start_time: Start time for duration calculation
        """
        duration_ms = int((time.time() - start_time) * 1000)
        entry = ActivityLogEntry(
            timestamp=datetime.now(),
            action_type=ActionType.ERROR,
            item_id=item_id,
            outcome=Outcome.FAILURE,
            duration_ms=duration_ms,
            details=error,
        )
        self.activity_logger.log(entry)

    def _quarantine_item(self, item_path: Path, error: str) -> None:
        """Move item to quarantine folder.

        Args:
            item_path: Path to the item
            error: Error message
        """
        try:
            if not item_path.exists():
                return

            self.vault_config.quarantine.mkdir(parents=True, exist_ok=True)

            # Read and update frontmatter
            content = item_path.read_text()
            frontmatter, body = parse_frontmatter(content)

            if frontmatter:
                frontmatter["status"] = "quarantined"
                frontmatter["error"] = error
                content = generate_frontmatter(frontmatter, body)

            # Move to quarantine
            dest_path = self.vault_config.quarantine / item_path.name
            dest_path.write_text(content)
            item_path.unlink()

        except Exception:
            # Best effort - just move the file
            try:
                shutil.move(str(item_path), str(self.vault_config.quarantine))
            except Exception:
                pass

    def process_all(self) -> tuple[int, int]:
        """Process all pending items.

        Returns:
            Tuple of (success_count, failure_count)
        """
        items = self.get_pending_items()
        success_count = 0
        failure_count = 0

        for item_path in items:
            if self.process_item(item_path):
                success_count += 1
            else:
                failure_count += 1

        return success_count, failure_count

    def update_dashboard(self) -> None:
        """Update Dashboard.md after processing."""
        from ai_employee.services.dashboard import DashboardService

        dashboard_service = DashboardService(self.vault_config)
        dashboard_service.update_dashboard()
