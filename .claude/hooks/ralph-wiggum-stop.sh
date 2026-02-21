#!/usr/bin/env bash
# Ralph Wiggum Stop Hook - delegates to Python module
#
# Checks if an active autonomous task exists before allowing Claude to exit.
# If a task is still in progress, this hook blocks the exit and re-injects
# the task prompt + context to stdout so Claude can continue working.
#
# Exit codes:
#   0 - Allow exit (no active task, or task is terminal/paused)
#   1 - Block exit (active task in progress, output re-injection prompt)

python3 -m ai_employee.cli.ralph_stop_hook --vault "${VAULT_PATH:-$HOME/AI_Employee_Vault}"
