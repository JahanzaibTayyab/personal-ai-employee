"""Unit tests for the Ralph Wiggum stop hook logic."""

import json
from pathlib import Path

import pytest

from ai_employee.cli.ralph_stop_hook import check_active_tasks


class TestStopHookAllowExit:
    """Tests for cases where exit should be allowed (return 0)."""

    def test_no_active_tasks_dir(self, tmp_path: Path) -> None:
        """Test that missing Active_Tasks directory allows exit."""
        result = check_active_tasks(tmp_path)
        assert result == 0

    def test_empty_active_tasks_dir(self, tmp_path: Path) -> None:
        """Test that empty Active_Tasks directory allows exit."""
        (tmp_path / "Active_Tasks").mkdir()
        result = check_active_tasks(tmp_path)
        assert result == 0

    def test_completed_task_allows_exit(self, tmp_path: Path) -> None:
        """Test that a completed task allows exit."""
        active_dir = tmp_path / "Active_Tasks"
        active_dir.mkdir()
        task = {
            "task_id": "test-123",
            "status": "completed",
            "prompt": "Done task",
            "iteration": 3,
            "max_iterations": 10,
        }
        (active_dir / "test-123.json").write_text(json.dumps(task))

        result = check_active_tasks(tmp_path)
        assert result == 0

    def test_failed_task_allows_exit(self, tmp_path: Path) -> None:
        """Test that a failed task allows exit."""
        active_dir = tmp_path / "Active_Tasks"
        active_dir.mkdir()
        task = {
            "task_id": "test-456",
            "status": "failed",
            "prompt": "Failed task",
            "iteration": 2,
            "max_iterations": 10,
        }
        (active_dir / "test-456.json").write_text(json.dumps(task))

        result = check_active_tasks(tmp_path)
        assert result == 0

    def test_paused_task_allows_exit(self, tmp_path: Path) -> None:
        """Test that a paused task allows exit."""
        active_dir = tmp_path / "Active_Tasks"
        active_dir.mkdir()
        task = {
            "task_id": "test-789",
            "status": "paused",
            "prompt": "Paused for approval",
            "iteration": 1,
            "max_iterations": 10,
        }
        (active_dir / "test-789.json").write_text(json.dumps(task))

        result = check_active_tasks(tmp_path)
        assert result == 0

    def test_invalid_json_allows_exit(self, tmp_path: Path) -> None:
        """Test that invalid JSON files are skipped gracefully."""
        active_dir = tmp_path / "Active_Tasks"
        active_dir.mkdir()
        (active_dir / "bad-file.json").write_text("not valid json {{{")

        result = check_active_tasks(tmp_path)
        assert result == 0

    def test_unknown_status_allows_exit(self, tmp_path: Path) -> None:
        """Test that unknown status values allow exit."""
        active_dir = tmp_path / "Active_Tasks"
        active_dir.mkdir()
        task = {
            "task_id": "test-unknown",
            "status": "something_weird",
            "prompt": "Unknown status",
        }
        (active_dir / "test-unknown.json").write_text(json.dumps(task))

        result = check_active_tasks(tmp_path)
        assert result == 0


class TestStopHookBlockExit:
    """Tests for cases where exit should be blocked (return 1)."""

    def test_in_progress_task_blocks_exit(self, tmp_path: Path) -> None:
        """Test that an in_progress task blocks exit."""
        active_dir = tmp_path / "Active_Tasks"
        active_dir.mkdir()
        task = {
            "task_id": "active-001",
            "status": "in_progress",
            "prompt": "Process inbox items",
            "iteration": 2,
            "max_iterations": 10,
            "context": "Read 3 emails",
        }
        (active_dir / "active-001.json").write_text(json.dumps(task))

        result = check_active_tasks(tmp_path)
        assert result == 1

    def test_in_progress_outputs_task_info(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that blocking exit outputs task information."""
        active_dir = tmp_path / "Active_Tasks"
        active_dir.mkdir()
        task = {
            "task_id": "active-002",
            "status": "in_progress",
            "prompt": "Draft email replies",
            "iteration": 5,
            "max_iterations": 10,
            "context": "Drafted reply for item 3",
        }
        (active_dir / "active-002.json").write_text(json.dumps(task))

        check_active_tasks(tmp_path)

        captured = capsys.readouterr()
        assert "ACTIVE TASK DETECTED" in captured.out
        assert "active-002" in captured.out
        assert "5/10" in captured.out
        assert "Draft email replies" in captured.out
        assert "Drafted reply for item 3" in captured.out
        assert "TASK_COMPLETE" in captured.out

    def test_in_progress_without_context(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test output for task without context."""
        active_dir = tmp_path / "Active_Tasks"
        active_dir.mkdir()
        task = {
            "task_id": "active-003",
            "status": "in_progress",
            "prompt": "New task",
            "iteration": 1,
            "max_iterations": 10,
        }
        (active_dir / "active-003.json").write_text(json.dumps(task))

        check_active_tasks(tmp_path)

        captured = capsys.readouterr()
        assert "ACTIVE TASK DETECTED" in captured.out
        assert "Last context" not in captured.out
