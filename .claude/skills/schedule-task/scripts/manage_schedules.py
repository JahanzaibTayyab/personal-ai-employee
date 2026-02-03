#!/usr/bin/env python3
"""Manage scheduled tasks using SchedulerService."""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_vault_path() -> Path:
    """Get vault path from environment or default."""
    vault = os.environ.get("VAULT_PATH", "~/AI_Employee_Vault")
    return Path(vault).expanduser()


def use_service(vault: Path) -> bool:
    """Check if SchedulerService is available."""
    try:
        from ai_employee.services.scheduler import SchedulerService
        return True
    except ImportError:
        return False


def list_schedules_via_service(vault: Path) -> dict:
    """List all scheduled tasks using SchedulerService."""
    from ai_employee.config import VaultConfig
    from ai_employee.services.scheduler import SchedulerService

    config = VaultConfig(root=vault)
    service = SchedulerService(config)

    tasks = service.get_all_tasks()

    return {
        "success": True,
        "count": len(tasks),
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "schedule": t.schedule,
                "enabled": t.enabled,
                "timezone": t.timezone,
                "last_run": t.last_run.isoformat() if t.last_run else None,
                "next_run": t.next_run.isoformat() if t.next_run else None,
                "type": t.action.get("type", "custom"),
            }
            for t in tasks
        ]
    }


def create_schedule_via_service(
    name: str,
    schedule: str,
    action_type: str,
    timezone: str,
    missed: str,
    vault: Path
) -> dict:
    """Create a new scheduled task using SchedulerService."""
    from ai_employee.config import VaultConfig
    from ai_employee.services.scheduler import SchedulerService
    from ai_employee.models.scheduled_task import ScheduledTask, TaskType, MissedStrategy

    config = VaultConfig(root=vault)
    service = SchedulerService(config)

    # Map action type to TaskType
    type_map = {
        "briefing": TaskType.BRIEFING,
        "audit": TaskType.AUDIT,
        "update_dashboard": TaskType.UPDATE_DASHBOARD,
        "check_approvals": TaskType.CHECK_APPROVALS,
        "custom": TaskType.CUSTOM,
    }
    task_type = type_map.get(action_type.lower(), TaskType.CUSTOM)

    # Map missed strategy
    strategy_map = {
        "skip": MissedStrategy.SKIP,
        "run": MissedStrategy.RUN_IMMEDIATELY,
        "run_immediately": MissedStrategy.RUN_IMMEDIATELY,
        "queue": MissedStrategy.QUEUE,
    }
    strategy = strategy_map.get(missed.lower(), MissedStrategy.RUN_IMMEDIATELY)

    task = ScheduledTask.create(
        name=name,
        schedule=schedule,
        task_type=task_type,
        timezone=timezone,
        missed_strategy=strategy,
    )

    success = service.add_task(task)

    return {
        "success": success,
        "task_id": task.id,
        "name": name,
        "schedule": schedule,
        "timezone": timezone,
        "type": task_type.value,
    }


def toggle_schedule_via_service(task_id: str, enabled: bool, vault: Path) -> dict:
    """Enable or disable a scheduled task using SchedulerService."""
    from ai_employee.config import VaultConfig
    from ai_employee.services.scheduler import SchedulerService

    config = VaultConfig(root=vault)
    service = SchedulerService(config)

    if enabled:
        success = service.enable_task(task_id)
    else:
        success = service.disable_task(task_id)

    if success:
        return {
            "success": True,
            "task_id": task_id,
            "enabled": enabled,
        }
    return {"success": False, "error": f"Task not found: {task_id}"}


def delete_schedule_via_service(task_id: str, vault: Path) -> dict:
    """Delete a scheduled task using SchedulerService."""
    from ai_employee.config import VaultConfig
    from ai_employee.services.scheduler import SchedulerService

    config = VaultConfig(root=vault)
    service = SchedulerService(config)

    success = service.remove_task(task_id)

    if success:
        return {
            "success": True,
            "task_id": task_id,
            "action": "deleted",
        }
    return {"success": False, "error": f"Task not found: {task_id}"}


def run_task_via_service(task_id: str, vault: Path) -> dict:
    """Run a scheduled task immediately using SchedulerService."""
    from ai_employee.config import VaultConfig
    from ai_employee.services.scheduler import SchedulerService

    config = VaultConfig(root=vault)
    service = SchedulerService(config)

    result = service.run_task(task_id)
    return result


def get_missed_tasks_via_service(vault: Path) -> dict:
    """Get all missed tasks using SchedulerService."""
    from ai_employee.config import VaultConfig
    from ai_employee.services.scheduler import SchedulerService

    config = VaultConfig(root=vault)
    service = SchedulerService(config)

    missed = service.get_missed_tasks()

    return {
        "success": True,
        "count": len(missed),
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "schedule": t.schedule,
                "next_run": t.next_run.isoformat() if t.next_run else None,
                "missed_strategy": t.missed_strategy.value,
            }
            for t in missed
        ]
    }


# Fallback implementations for standalone mode
def list_schedules_standalone(vault: Path) -> dict:
    """List all scheduled tasks (standalone mode)."""
    schedules_dir = vault / "Schedules"

    if not schedules_dir.exists():
        return {"success": True, "count": 0, "tasks": []}

    tasks = []
    for file in schedules_dir.glob("*.md"):
        content = file.read_text()
        fm = parse_frontmatter_simple(content)

        tasks.append({
            "id": fm.get("id", file.stem),
            "name": fm.get("name", file.stem),
            "schedule": fm.get("schedule", ""),
            "enabled": fm.get("enabled", True),
            "last_run": fm.get("last_run"),
            "next_run": fm.get("next_run"),
        })

    tasks.sort(key=lambda x: x.get("name", ""))
    return {"success": True, "count": len(tasks), "tasks": tasks, "mode": "standalone"}


def parse_frontmatter_simple(content: str) -> dict:
    """Parse YAML frontmatter from markdown file."""
    if not content.startswith("---"):
        return {}

    end = content.find("---", 3)
    if end == -1:
        return {}

    frontmatter = content[3:end].strip()
    result = {}

    for line in frontmatter.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            result[key] = value

    return result


def create_schedule_standalone(
    name: str,
    schedule: str,
    action_type: str,
    timezone: str,
    missed: str,
    vault: Path
) -> dict:
    """Create a new scheduled task (standalone mode)."""
    schedules_dir = vault / "Schedules"
    schedules_dir.mkdir(parents=True, exist_ok=True)

    task_id = "schedule_" + name.lower().replace(" ", "_")
    now = datetime.now()
    is_cron = " " in schedule

    content = f"""---
id: "{task_id}"
name: "{name}"
schedule: "{schedule}"
timezone: "{timezone}"
enabled: true
missed_strategy: "{missed}"
created_at: "{now.isoformat()}"
action:
  type: "{action_type}"
---

## Scheduled Task: {name}

**Schedule**: {schedule}
**Timezone**: {timezone}
**Type**: {"Recurring (cron)" if is_cron else "One-time"}
**Missed Strategy**: {missed}
"""

    task_file = schedules_dir / f"{task_id}.md"
    task_file.write_text(content)

    return {
        "success": True,
        "task_id": task_id,
        "name": name,
        "schedule": schedule,
        "mode": "standalone",
    }


def main():
    parser = argparse.ArgumentParser(description="Manage scheduled tasks")
    parser.add_argument("action", choices=["list", "create", "enable", "disable", "delete", "run", "missed"],
                       nargs="?", default="list", help="Action to perform")
    parser.add_argument("--id", help="Task ID")
    parser.add_argument("--name", help="Task name (for create)")
    parser.add_argument("--schedule", help="Cron expression or ISO datetime")
    parser.add_argument("--action-type", default="custom", help="Action type (briefing, audit, custom)")
    parser.add_argument("--timezone", default="local", help="Timezone")
    parser.add_argument("--missed", default="run", choices=["skip", "run", "queue"],
                       help="Missed schedule strategy")
    parser.add_argument("--vault", help="Vault path override")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--standalone", action="store_true", help="Use standalone mode (skip service)")

    args = parser.parse_args()
    vault = Path(args.vault).expanduser() if args.vault else get_vault_path()

    # Determine mode
    service_available = not args.standalone and use_service(vault)

    if args.action == "list":
        if service_available:
            result = list_schedules_via_service(vault)
        else:
            result = list_schedules_standalone(vault)

    elif args.action == "create":
        if not args.name or not args.schedule:
            print("Error: --name and --schedule required for create", file=sys.stderr)
            sys.exit(1)
        if service_available:
            result = create_schedule_via_service(
                args.name, args.schedule, args.action_type,
                args.timezone, args.missed, vault
            )
        else:
            result = create_schedule_standalone(
                args.name, args.schedule, args.action_type,
                args.timezone, args.missed, vault
            )

    elif args.action == "enable":
        if not args.id:
            print("Error: --id required", file=sys.stderr)
            sys.exit(1)
        if service_available:
            result = toggle_schedule_via_service(args.id, True, vault)
        else:
            result = {"success": False, "error": "Service required for enable/disable"}

    elif args.action == "disable":
        if not args.id:
            print("Error: --id required", file=sys.stderr)
            sys.exit(1)
        if service_available:
            result = toggle_schedule_via_service(args.id, False, vault)
        else:
            result = {"success": False, "error": "Service required for enable/disable"}

    elif args.action == "delete":
        if not args.id:
            print("Error: --id required", file=sys.stderr)
            sys.exit(1)
        if service_available:
            result = delete_schedule_via_service(args.id, vault)
        else:
            result = {"success": False, "error": "Service required for delete"}

    elif args.action == "run":
        if not args.id:
            print("Error: --id required", file=sys.stderr)
            sys.exit(1)
        if service_available:
            result = run_task_via_service(args.id, vault)
        else:
            result = {"success": False, "error": "Service required for run"}

    elif args.action == "missed":
        if service_available:
            result = get_missed_tasks_via_service(vault)
        else:
            result = {"success": False, "error": "Service required for missed check"}

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if args.action == "list":
            if result["count"] == 0:
                print("No scheduled tasks.")
            else:
                print(f"Scheduled Tasks ({result['count']})")
                if result.get("mode") == "standalone":
                    print("(standalone mode)")
                print()
                for t in result["tasks"]:
                    status = "Enabled" if t.get("enabled") else "Disabled"
                    print(f"  - {t['name']} ({t['id']})")
                    print(f"    Schedule: {t['schedule']}")
                    print(f"    Status: {status}")
                    if t.get("type"):
                        print(f"    Type: {t['type']}")
                    print()

        elif args.action == "missed":
            if result.get("success"):
                if result["count"] == 0:
                    print("No missed tasks.")
                else:
                    print(f"Missed Tasks ({result['count']})")
                    for t in result["tasks"]:
                        print(f"  - {t['name']} ({t['id']})")
                        print(f"    Should have run: {t['next_run']}")
                        print(f"    Strategy: {t['missed_strategy']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif result.get("success"):
            if args.action == "create":
                print(f"Task created: {result['name']}")
                print(f"   ID: {result['task_id']}")
                print(f"   Schedule: {result['schedule']}")
            elif args.action in ("enable", "disable"):
                status = "enabled" if result.get("enabled") else "disabled"
                print(f"Task {status}: {result['task_id']}")
            elif args.action == "delete":
                print(f"Task deleted: {result['task_id']}")
            elif args.action == "run":
                print(f"Task executed: {args.id}")
                if result.get("message"):
                    print(f"   Result: {result['message']}")
        else:
            print(f"Error: {result.get('error')}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
