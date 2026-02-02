"""File System Watcher - monitors /Drop folder for new files."""

import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from watchdog.events import DirCreatedEvent, FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from ai_employee.config import VaultConfig
from ai_employee.models.action_item import (
    ActionItem,
    ActionItemStatus,
    ActionItemType,
    Priority,
    SourceType,
)
from ai_employee.models.watcher_event import EventType, WatcherEvent
from ai_employee.models.watcher_event import SourceType as WatcherSourceType
from ai_employee.services.handbook import detect_priority_from_text
from ai_employee.utils.frontmatter import generate_frontmatter
from ai_employee.watchers.base import BaseWatcher


class FileDropHandler(FileSystemEventHandler):
    """Handler for file creation events in the Drop folder."""

    def __init__(self, watcher: "FileSystemWatcher"):
        """Initialize the handler.

        Args:
            watcher: The parent FileSystemWatcher instance
        """
        self.watcher = watcher

    def on_created(self, event: FileCreatedEvent | DirCreatedEvent) -> None:
        """Handle file creation event.

        Args:
            event: The file creation event
        """
        if event.is_directory:
            return

        # Add small delay to ensure file is fully written
        time.sleep(0.5)

        file_path = Path(str(event.src_path))
        self.watcher.handle_new_file(file_path)


class FileSystemWatcher(BaseWatcher):
    """Watcher for the /Drop folder that queues files for processing."""

    SUPPORTED_EXTENSIONS = {
        ".txt", ".pdf", ".docx", ".png", ".jpg", ".jpeg",
        ".csv", ".json", ".md", ".xlsx", ".doc"
    }

    def __init__(self, vault_config: VaultConfig):
        """Initialize the file system watcher.

        Args:
            vault_config: Vault configuration with paths
        """
        super().__init__(vault_config.root, WatcherSourceType.FILESYSTEM)
        self.vault_config = vault_config
        self.observer: Any = None

    def start(self) -> None:
        """Start watching the Drop folder."""
        if self.running:
            return

        # Ensure vault structure exists
        self.vault_config.ensure_structure()

        # Set up the observer
        self.observer = Observer()
        handler = FileDropHandler(self)
        self.observer.schedule(handler, str(self.vault_config.drop), recursive=False)

        # Start observer in a thread
        self.observer.start()
        self.running = True

        # Log start event
        self.log_event(
            EventType.STARTED,
            str(self.vault_config.drop),
            {"message": "File system watcher started"}
        )

    def stop(self) -> None:
        """Stop watching the Drop folder."""
        if not self.running:
            return

        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        self.running = False

        # Log stop event
        self.log_event(
            EventType.STOPPED,
            str(self.vault_config.drop),
            {"message": "File system watcher stopped"}
        )

    def handle_new_file(self, file_path: Path) -> None:
        """Handle a newly detected file.

        Args:
            file_path: Path to the new file
        """
        try:
            if not file_path.exists():
                return

            # Check file extension
            ext = file_path.suffix.lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                self._quarantine_file(
                    file_path,
                    f"Unsupported file type: {ext}"
                )
                return

            # Get file metadata
            stat = file_path.stat()
            file_size = stat.st_size

            # Check file size (10MB limit)
            if file_size > 10 * 1024 * 1024:
                self._quarantine_file(
                    file_path,
                    f"File too large: {file_size} bytes (>10MB)"
                )
                return

            # Create action item
            action_item = ActionItem(
                type=ActionItemType.FILE_DROP,
                source=SourceType.FILESYSTEM,
                original_name=file_path.name,
                created=datetime.now(),
                status=ActionItemStatus.PENDING,
                priority=detect_priority_from_text(file_path.name),
                file_size=file_size,
                file_type=ext,
            )

            # Generate action item filename
            action_filename = action_item.get_filename()
            action_path = self.vault_config.needs_action / action_filename

            # Read file content for small text files
            content = ""
            if ext in {".txt", ".md", ".json", ".csv"} and file_size < 100000:
                try:
                    content = file_path.read_text()
                except Exception:
                    content = f"[Binary or unreadable content from {file_path.name}]"
            else:
                content = f"[File content: {file_path.name} ({file_size} bytes)]"

            # Generate markdown with frontmatter
            frontmatter = action_item.to_frontmatter()
            markdown_content = generate_frontmatter(frontmatter, f"## Content\n\n{content}")

            # Write action item file
            action_path.write_text(markdown_content)

            # Move original file to Done (or delete based on policy)
            # For now, we delete the original after creating action item
            file_path.unlink()

            # Log success event
            self.log_event(
                EventType.CREATED,
                str(file_path),
                {
                    "size": file_size,
                    "file_type": ext,
                    "action_item": action_filename,
                }
            )

        except Exception as e:
            self._quarantine_file(file_path, str(e))

    def _quarantine_file(self, file_path: Path, error: str) -> None:
        """Move file to quarantine with error metadata.

        Args:
            file_path: Path to the file
            error: Error message
        """
        try:
            if not file_path.exists():
                return

            # Ensure quarantine folder exists
            self.vault_config.quarantine.mkdir(parents=True, exist_ok=True)

            # Move file to quarantine
            dest_path = self.vault_config.quarantine / file_path.name
            shutil.move(str(file_path), str(dest_path))

            # Create error metadata file
            error_item = ActionItem(
                type=ActionItemType.FILE_DROP,
                source=SourceType.FILESYSTEM,
                original_name=file_path.name,
                created=datetime.now(),
                status=ActionItemStatus.QUARANTINED,
                priority=Priority.NORMAL,
                error=error,
            )

            error_path = self.vault_config.quarantine / f"{file_path.name}.error.md"
            frontmatter = error_item.to_frontmatter()
            error_content = generate_frontmatter(frontmatter, f"## Error\n\n{error}")
            error_path.write_text(error_content)

            # Log error event
            self.log_event(
                EventType.ERROR,
                str(file_path),
                {"error_message": error}
            )

        except Exception as e:
            # Log the quarantine failure
            self.log_event(
                EventType.ERROR,
                str(file_path),
                {"error_message": f"Failed to quarantine: {e}"}
            )

    def process_event(self, event: WatcherEvent) -> None:
        """Process a detected event (not used directly, events go through handler)."""
        pass


def run_watcher(vault_path: Path, interval: int = 60) -> None:
    """Run the file system watcher continuously.

    Args:
        vault_path: Path to the Obsidian vault
        interval: Check interval in seconds (used for keep-alive logging)
    """
    from ai_employee.config import VaultConfig

    config = VaultConfig(root=vault_path)
    watcher = FileSystemWatcher(config)

    print(f"Starting file system watcher on {config.drop}")
    watcher.start()

    try:
        while True:
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        watcher.stop()
        print("Watcher stopped.")
