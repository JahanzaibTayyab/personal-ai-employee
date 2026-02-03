"""Approval folder watcher.

Monitors approval folders for file changes:
- /Pending_Approval/ for new requests
- /Approved/ for user approvals
- /Rejected/ for user rejections
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from watchdog.events import DirMovedEvent, FileMovedEvent, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from ai_employee.config import VaultConfig
from ai_employee.models.approval_request import ApprovalRequest
from ai_employee.models.watcher_event import EventType, SourceType, WatcherEvent
from ai_employee.services.approval import ApprovalService
from ai_employee.watchers.base import BaseWatcher


class ApprovalEventHandler(FileSystemEventHandler):
    """Handler for approval folder file system events."""

    def __init__(
        self,
        watcher: "ApprovalWatcher",
        vault_config: VaultConfig,
    ) -> None:
        """Initialize the handler."""
        super().__init__()
        self._watcher = watcher
        self._config = vault_config
        self._service = ApprovalService(vault_config)

    def _is_approval_file(self, path: Path) -> bool:
        """Check if file is an approval request file."""
        return path.name.startswith("APPROVAL_") and path.suffix == ".md"

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if not self._is_approval_file(path):
            return

        # Check which folder the file was created in
        parent = path.parent.name

        if parent == "Pending_Approval":
            self._watcher._on_approval_created(path)
        elif parent == "Approved":
            self._watcher._on_approval_approved(path)
        elif parent == "Rejected":
            self._watcher._on_approval_rejected(path)

    def on_moved(self, event: FileMovedEvent) -> None:
        """Handle file move events (user approval/rejection)."""
        if event.is_directory:
            return

        src_path = Path(event.src_path)
        dest_path = Path(event.dest_path)

        if not self._is_approval_file(dest_path):
            return

        dest_parent = dest_path.parent.name

        if dest_parent == "Approved":
            self._watcher._on_approval_approved(dest_path)
        elif dest_parent == "Rejected":
            self._watcher._on_approval_rejected(dest_path)


class ApprovalWatcher(BaseWatcher):
    """Watches approval folders for changes."""

    def __init__(self, vault_config: VaultConfig) -> None:
        """Initialize approval folder watcher."""
        super().__init__(vault_config.root, SourceType.APPROVAL)
        self._config = vault_config
        self._observer: Observer | None = None
        self._service = ApprovalService(vault_config)

        # Callback hooks for external consumers
        self.on_approval_created: Callable[[ApprovalRequest], None] | None = None
        self.on_approval_approved: Callable[[ApprovalRequest], None] | None = None
        self.on_approval_rejected: Callable[[ApprovalRequest], None] | None = None

    def start(self) -> None:
        """Start watching approval folders."""
        if self.running:
            return

        self._observer = Observer()
        handler = ApprovalEventHandler(self, self._config)

        # Watch all approval-related folders
        folders = [
            self._config.pending_approval,
            self._config.approved,
            self._config.rejected,
        ]

        for folder in folders:
            if folder.exists():
                self._observer.schedule(handler, str(folder), recursive=False)

        self._observer.start()
        self.running = True

        self.log_event(
            EventType.DETECTED,
            "approval_watcher",
            {"status": "started"},
        )

    def stop(self) -> None:
        """Stop watching approval folders."""
        if not self.running or self._observer is None:
            return

        self._observer.stop()
        self._observer.join()
        self._observer = None
        self.running = False

        self.log_event(
            EventType.DETECTED,
            "approval_watcher",
            {"status": "stopped"},
        )

    def process_event(self, event: WatcherEvent) -> None:
        """Process a detected event."""
        # Events are processed through callbacks
        pass

    def _read_approval_from_file(self, path: Path) -> ApprovalRequest | None:
        """Read approval request from file."""
        from ai_employee.utils.frontmatter import parse_frontmatter

        if not path.exists():
            return None

        content = path.read_text()
        frontmatter, _ = parse_frontmatter(content)

        if not frontmatter:
            return None

        return ApprovalRequest.from_frontmatter(frontmatter)

    def _on_approval_created(self, path: Path) -> None:
        """Handle new approval request creation."""
        request = self._read_approval_from_file(path)
        if request is None:
            return

        self.log_event(
            EventType.DETECTED,
            request.id,
            {
                "action": "created",
                "category": request.category.value,
                "expires_at": request.expires_at.isoformat(),
            },
        )

        if self.on_approval_created:
            self.on_approval_created(request)

    def _on_approval_approved(self, path: Path) -> None:
        """Handle approval event (file moved to /Approved/)."""
        request = self._read_approval_from_file(path)
        if request is None:
            return

        self.log_event(
            EventType.PROCESSED,
            request.id,
            {
                "action": "approved",
                "category": request.category.value,
            },
        )

        if self.on_approval_approved:
            self.on_approval_approved(request)

    def _on_approval_rejected(self, path: Path) -> None:
        """Handle rejection event (file moved to /Rejected/)."""
        request = self._read_approval_from_file(path)
        if request is None:
            return

        self.log_event(
            EventType.PROCESSED,
            request.id,
            {
                "action": "rejected",
                "category": request.category.value,
                "status": request.status.value,
            },
        )

        if self.on_approval_rejected:
            self.on_approval_rejected(request)

    def process_pending_queue(self) -> tuple[int, int]:
        """Process all pending approved requests.

        Returns:
            Tuple of (success_count, failure_count)
        """
        return self._service.process_approval_queue()
