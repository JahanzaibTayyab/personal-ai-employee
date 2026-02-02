"""JSON lines logger utility for activity and watcher logs."""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T")


class JsonlLogger(Generic[T]):
    """Logger that writes to JSON lines format files.

    Files are named with date suffix: {prefix}_YYYY-MM-DD.log
    """

    def __init__(
        self,
        logs_dir: Path,
        prefix: str,
        serializer: Callable[[T], str],
        deserializer: Callable[[str], T],
    ):
        """Initialize the logger.

        Args:
            logs_dir: Directory to write log files
            prefix: Prefix for log filenames (e.g., 'claude', 'watcher')
            serializer: Function to convert entry to JSON string
            deserializer: Function to convert JSON string to entry
        """
        self.logs_dir = logs_dir
        self.prefix = prefix
        self.serializer = serializer
        self.deserializer = deserializer

    def _get_log_path(self, date: datetime | None = None) -> Path:
        """Get log file path for a specific date."""
        if date is None:
            date = datetime.now()
        filename = f"{self.prefix}_{date.strftime('%Y-%m-%d')}.log"
        return self.logs_dir / filename

    def log(self, entry: T, date: datetime | None = None) -> None:
        """Append entry to the log file.

        Args:
            entry: Entry to log
            date: Optional date for the log file (defaults to today)
        """
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = self._get_log_path(date)

        json_line = self.serializer(entry)

        with open(log_path, "a") as f:
            f.write(json_line + "\n")

    def read_entries(self, date: datetime | None = None) -> list[T]:
        """Read all entries from a log file.

        Args:
            date: Optional date to read from (defaults to today)

        Returns:
            List of entries from the log file
        """
        log_path = self._get_log_path(date)

        if not log_path.exists():
            return []

        entries = []
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(self.deserializer(line))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue

        return entries

    def read_recent(self, count: int = 10, date: datetime | None = None) -> list[T]:
        """Read the most recent entries from a log file.

        Args:
            count: Number of entries to return
            date: Optional date to read from (defaults to today)

        Returns:
            List of most recent entries (newest first)
        """
        entries = self.read_entries(date)
        return list(reversed(entries[-count:]))

    def get_available_dates(self) -> list[datetime]:
        """Get list of dates that have log files.

        Returns:
            List of dates with log files, newest first
        """
        if not self.logs_dir.exists():
            return []

        dates = []
        for log_file in self.logs_dir.glob(f"{self.prefix}_*.log"):
            try:
                date_str = log_file.stem.replace(f"{self.prefix}_", "")
                date = datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date)
            except ValueError:
                continue

        return sorted(dates, reverse=True)
