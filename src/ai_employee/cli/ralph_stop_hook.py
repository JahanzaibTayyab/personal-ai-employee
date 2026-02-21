#!/usr/bin/env python3
"""Ralph Wiggum Stop Hook - checks for active tasks before allowing exit.

This module provides the logic for the stop hook that prevents Claude
from exiting while a task is still in progress. It reads task state files
from /Active_Tasks/ and determines if exit should be blocked.

Usage as a script:
    python -m ai_employee.cli.ralph_stop_hook [--vault /path/to/vault]

Exit codes:
    0 - Allow exit (no active task, or task is terminal/paused)
    1 - Block exit (active task in progress, output re-injection prompt)

To register as a Claude stop hook, create .claude/hooks/ralph-wiggum-stop.sh:
    #!/usr/bin/env bash
    python3 -m ai_employee.cli.ralph_stop_hook --vault "${VAULT_PATH:-$HOME/AI_Employee_Vault}"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def check_active_tasks(vault_path: Path) -> int:
    """Check for active tasks and determine whether to allow exit.

    Args:
        vault_path: Path to the AI Employee vault.

    Returns:
        0 to allow exit, 1 to block exit.
    """
    active_tasks_dir = vault_path / "Active_Tasks"

    if not active_tasks_dir.is_dir():
        return 0

    task_files = sorted(active_tasks_dir.glob("*.json"))
    if not task_files:
        return 0

    for task_file in task_files:
        try:
            data = json.loads(task_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        status = data.get("status", "unknown")

        # Terminal states: allow exit
        if status in ("completed", "failed"):
            continue

        # Paused for approval: allow exit (human must act)
        if status == "paused":
            continue

        # In-progress: block exit and re-inject task
        if status == "in_progress":
            prompt = data.get("prompt", "Unknown task")
            context = data.get("context", "")
            iteration = data.get("iteration", 0)
            max_iter = data.get("max_iterations", 10)
            task_id = data.get("task_id", "unknown")

            print("ACTIVE TASK DETECTED - Cannot exit.")
            print(f"Task ID: {task_id}")
            print(f"Iteration: {iteration}/{max_iter}")
            print(f"Prompt: {prompt}")
            if context:
                print(f"Last context: {context}")
            print()
            print(
                "Continue working on this task. "
                "When complete, signal TASK_COMPLETE."
            )
            return 1

    # No blocking tasks found
    return 0


def main() -> None:
    """Entry point for the stop hook script."""
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum stop hook - check for active tasks"
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=Path.home() / "AI_Employee_Vault",
        help="Path to the AI Employee vault",
    )
    args = parser.parse_args()

    vault_path = args.vault.expanduser().resolve()
    exit_code = check_active_tasks(vault_path)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
