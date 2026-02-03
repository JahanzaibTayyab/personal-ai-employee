"""CLI entry point for AI Employee commands."""

import argparse
import sys
from pathlib import Path


def cmd_watch(args: argparse.Namespace) -> int:
    """Run the file system watcher command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from ai_employee.watchers.filesystem import run_watcher

    vault_path = Path(args.vault).expanduser().resolve()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        print("Please create the vault first or specify a valid path.")
        return 1

    print("Starting AI Employee File Watcher")
    print(f"Vault: {vault_path}")
    print(f"Watching: {vault_path / 'Drop'}")
    print("Press Ctrl+C to stop.\n")

    run_watcher(vault_path, interval=args.interval)
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Update the dashboard command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from ai_employee.config import VaultConfig
    from ai_employee.services.dashboard import DashboardService

    vault_path = Path(args.vault).expanduser().resolve()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return 1

    config = VaultConfig(root=vault_path)
    service = DashboardService(config)

    service.update_dashboard()
    print(f"Dashboard updated: {config.dashboard}")
    return 0


def cmd_gmail_watch(args: argparse.Namespace) -> int:
    """Run the Gmail watcher command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from ai_employee.watchers.gmail import run_gmail_watcher

    vault_path = Path(args.vault).expanduser().resolve()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        print("Please create the vault first or specify a valid path.")
        return 1

    credentials_path = None
    if args.credentials:
        credentials_path = Path(args.credentials).expanduser().resolve()
        if not credentials_path.exists():
            print(f"Error: Credentials file not found: {credentials_path}")
            return 1

    print("Starting AI Employee Gmail Watcher")
    print(f"Vault: {vault_path}")
    print(f"Poll interval: {args.interval} seconds")
    print("Press Ctrl+C to stop.\n")

    run_gmail_watcher(vault_path, credentials_path, args.interval)
    return 0


def cmd_watch_approvals(args: argparse.Namespace) -> int:
    """Run the approval watcher command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    import time

    from ai_employee.config import VaultConfig
    from ai_employee.services.approval import ApprovalService
    from ai_employee.watchers.approval import ApprovalWatcher

    vault_path = Path(args.vault).expanduser().resolve()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        print("Please create the vault first or specify a valid path.")
        return 1

    config = VaultConfig(root=vault_path)
    config.ensure_structure()

    # Ensure Silver tier folders exist
    config.pending_approval.mkdir(parents=True, exist_ok=True)
    config.approved.mkdir(parents=True, exist_ok=True)
    config.rejected.mkdir(parents=True, exist_ok=True)

    service = ApprovalService(config)
    watcher = ApprovalWatcher(config)

    # Set up callbacks
    def on_approved(request):
        print(f"[APPROVED] {request.category.value}: {request.id}")

    def on_rejected(request):
        print(f"[REJECTED] {request.category.value}: {request.id}")

    watcher.on_approval_approved = on_approved
    watcher.on_approval_rejected = on_rejected

    print("Starting AI Employee Approval Watcher")
    print(f"Vault: {vault_path}")
    print(f"Watching: {config.pending_approval}")
    print(f"Expiration check interval: {args.interval} seconds")
    print("Press Ctrl+C to stop.\n")

    watcher.start()

    try:
        while True:
            # Check for expired requests
            expired = service.check_expired_requests()
            if expired:
                for req in expired:
                    print(f"[EXPIRED] {req.category.value}: {req.id}")

            # Process any approved requests
            success, failure = watcher.process_pending_queue()
            if success or failure:
                print(f"[PROCESSED] {success} succeeded, {failure} failed")

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopping approval watcher...")
        watcher.stop()

    return 0


def cmd_watch_whatsapp(args: argparse.Namespace) -> int:
    """Run the WhatsApp watcher command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from ai_employee.config import VaultConfig
    from ai_employee.watchers.whatsapp import WhatsAppWatcher, WhatsAppWatcherStatus

    vault_path = Path(args.vault).expanduser().resolve()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        print("Please create the vault first or specify a valid path.")
        return 1

    config = VaultConfig(root=vault_path)
    config.ensure_structure()

    # Parse custom keywords if provided
    keywords = None
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",")]

    watcher = WhatsAppWatcher(config, keywords=keywords)

    # Set up callbacks
    def on_message(message):
        print(f"[DETECTED] {message.sender}: {message.content[:50]}...")
        print(f"           Keywords: {', '.join(message.keywords)}")

    def on_status(status):
        status_msg = {
            WhatsAppWatcherStatus.CONNECTING: "Connecting to WhatsApp Web...",
            WhatsAppWatcherStatus.QR_REQUIRED: "Please scan QR code in browser",
            WhatsAppWatcherStatus.CONNECTED: "Connected to WhatsApp",
            WhatsAppWatcherStatus.SESSION_EXPIRED: "Session expired - please reconnect",
            WhatsAppWatcherStatus.DISCONNECTED: "Disconnected",
            WhatsAppWatcherStatus.ERROR: "Error occurred",
        }
        print(f"[STATUS] {status_msg.get(status, status.value)}")

    watcher.on_message_detected = on_message
    watcher.on_status_change = on_status

    print("Starting AI Employee WhatsApp Watcher")
    print(f"Vault: {vault_path}")
    print(f"Keywords: {', '.join(watcher.keywords)}")
    print("Press Ctrl+C to stop.\n")

    try:
        watcher.start()
    except KeyboardInterrupt:
        print("\nStopping WhatsApp watcher...")
        watcher.stop()
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1

    return 0


def cmd_scheduler(args: argparse.Namespace) -> int:
    """Manage scheduled tasks command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from ai_employee.config import VaultConfig
    from ai_employee.services.scheduler import SchedulerService
    from ai_employee.models.scheduled_task import (
        ScheduledTask,
        TaskType,
        MissedStrategy,
        create_daily_briefing_task,
        create_weekly_audit_task,
    )

    vault_path = Path(args.vault).expanduser().resolve()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return 1

    config = VaultConfig(root=vault_path)
    config.ensure_structure()

    service = SchedulerService(config)

    if args.scheduler_cmd == "list":
        tasks = service.get_all_tasks()
        if not tasks:
            print("No scheduled tasks.")
        else:
            print(f"Scheduled Tasks ({len(tasks)})\n")
            for task in tasks:
                status = "Enabled" if task.enabled else "Disabled"
                print(f"  {task.name} ({task.id})")
                print(f"    Schedule: {task.schedule}")
                print(f"    Status: {status}")
                print(f"    Type: {task.action.get('type', 'custom')}")
                if task.last_run:
                    print(f"    Last run: {task.last_run.strftime('%Y-%m-%d %H:%M')}")
                print()

    elif args.scheduler_cmd == "add":
        # Map action type
        type_map = {
            "briefing": TaskType.BRIEFING,
            "audit": TaskType.AUDIT,
            "update_dashboard": TaskType.UPDATE_DASHBOARD,
            "check_approvals": TaskType.CHECK_APPROVALS,
            "custom": TaskType.CUSTOM,
        }
        task_type = type_map.get(args.type, TaskType.CUSTOM)

        # Map missed strategy
        strategy_map = {
            "skip": MissedStrategy.SKIP,
            "run": MissedStrategy.RUN_IMMEDIATELY,
            "queue": MissedStrategy.QUEUE,
        }
        strategy = strategy_map.get(args.missed, MissedStrategy.RUN_IMMEDIATELY)

        task = ScheduledTask.create(
            name=args.name,
            schedule=args.schedule,
            task_type=task_type,
            timezone=args.timezone,
            missed_strategy=strategy,
        )

        if service.add_task(task):
            print(f"Task created: {task.name}")
            print(f"  ID: {task.id}")
            print(f"  Schedule: {task.schedule}")
        else:
            print("Error: Failed to create task")
            return 1

    elif args.scheduler_cmd == "remove":
        if service.remove_task(args.id):
            print(f"Task removed: {args.id}")
        else:
            print(f"Error: Task not found: {args.id}")
            return 1

    elif args.scheduler_cmd == "run":
        result = service.run_task(args.id)
        if result.get("success"):
            print(f"Task executed: {args.id}")
            if result.get("message"):
                print(f"  Result: {result['message']}")
        else:
            print(f"Error: {result.get('error')}")
            return 1

    elif args.scheduler_cmd == "enable":
        if service.enable_task(args.id):
            print(f"Task enabled: {args.id}")
        else:
            print(f"Error: Task not found: {args.id}")
            return 1

    elif args.scheduler_cmd == "disable":
        if service.disable_task(args.id):
            print(f"Task disabled: {args.id}")
        else:
            print(f"Error: Task not found: {args.id}")
            return 1

    elif args.scheduler_cmd == "missed":
        missed = service.get_missed_tasks()
        if not missed:
            print("No missed tasks.")
        else:
            print(f"Missed Tasks ({len(missed)})\n")
            for task in missed:
                print(f"  {task.name} ({task.id})")
                print(f"    Should have run: {task.next_run}")
                print(f"    Strategy: {task.missed_strategy.value}")
                print()

    elif args.scheduler_cmd == "setup-defaults":
        # Create default briefing and audit tasks
        briefing = create_daily_briefing_task(hour=8, minute=0)
        audit = create_weekly_audit_task(day_of_week=0, hour=21)

        service.add_task(briefing)
        service.add_task(audit)

        print("Default scheduled tasks created:")
        print(f"  - {briefing.name}: {briefing.schedule}")
        print(f"  - {audit.name}: {audit.schedule}")

    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize the vault structure command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from ai_employee.config import VaultConfig

    vault_path = Path(args.vault).expanduser().resolve()

    config = VaultConfig(root=vault_path)
    config.ensure_structure()

    # Create initial Dashboard.md
    initial_dashboard = """# AI Employee Dashboard

**Last Updated**: Never

## Status

- **Watcher**: Not started
- **Pending Items**: 0
- **Processed Today**: 0

## Recent Activity

| Time | Action | Item | Result |
|------|--------|------|--------|
| - | - | - | - |

## Warnings

None

---
*Auto-generated by AI Employee*
"""

    if not config.dashboard.exists():
        config.dashboard.write_text(initial_dashboard)

    # Create initial Company_Handbook.md
    initial_handbook = """# Company Handbook

## Rules

### Rule 1: Priority Keywords
When processing items, check for these keywords and set priority:
- "urgent", "asap", "emergency" → priority: urgent
- "important", "priority" → priority: high

### Rule 2: Large File Handling
Files larger than 10MB should be flagged for manual review.

### Rule 3: Default Behavior
Process all items in order received (FIFO). Log all actions.

## Contact Information

Owner: [Your Name]
"""

    if not config.handbook.exists():
        config.handbook.write_text(initial_handbook)

    print(f"Vault initialized at: {vault_path}")
    print("Created folders:")
    print("  - Inbox/")
    print("  - Needs_Action/")
    print("  - Needs_Action/Email/")
    print("  - Done/")
    print("  - Drop/")
    print("  - Quarantine/")
    print("  - Logs/")
    print("Created files:")
    print("  - Dashboard.md")
    print("  - Company_Handbook.md")
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="ai-employee",
        description="Personal AI Employee - Autonomous Digital FTE",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )

    # Watch command
    watch_parser = subparsers.add_parser(
        "watch",
        help="Start the file system watcher",
    )
    watch_parser.add_argument(
        "--vault",
        type=str,
        default="~/AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ~/AI_Employee_Vault)",
    )
    watch_parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Keep-alive interval in seconds (default: 60)",
    )
    watch_parser.set_defaults(func=cmd_watch)

    # Dashboard command
    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="Update the Dashboard.md file",
    )
    dashboard_parser.add_argument(
        "--vault",
        type=str,
        default="~/AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ~/AI_Employee_Vault)",
    )
    dashboard_parser.set_defaults(func=cmd_dashboard)

    # Gmail watch command
    gmail_parser = subparsers.add_parser(
        "watch-gmail",
        help="Start the Gmail watcher",
    )
    gmail_parser.add_argument(
        "--vault",
        type=str,
        default="~/AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ~/AI_Employee_Vault)",
    )
    gmail_parser.add_argument(
        "--credentials",
        type=str,
        help="Path to Gmail OAuth2 credentials.json",
    )
    gmail_parser.add_argument(
        "--interval",
        type=int,
        default=120,
        help="Poll interval in seconds (default: 120)",
    )
    gmail_parser.set_defaults(func=cmd_gmail_watch)

    # Approval watch command
    approval_parser = subparsers.add_parser(
        "watch-approvals",
        help="Start the approval watcher",
    )
    approval_parser.add_argument(
        "--vault",
        type=str,
        default="~/AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ~/AI_Employee_Vault)",
    )
    approval_parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Expiration check interval in seconds (default: 60)",
    )
    approval_parser.set_defaults(func=cmd_watch_approvals)

    # WhatsApp watch command
    whatsapp_parser = subparsers.add_parser(
        "watch-whatsapp",
        help="Start the WhatsApp watcher",
    )
    whatsapp_parser.add_argument(
        "--vault",
        type=str,
        default="~/AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ~/AI_Employee_Vault)",
    )
    whatsapp_parser.add_argument(
        "--keywords",
        type=str,
        help="Comma-separated list of keywords (default: urgent,asap,invoice,payment,help,pricing)",
    )
    whatsapp_parser.set_defaults(func=cmd_watch_whatsapp)

    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize the vault structure",
    )
    init_parser.add_argument(
        "--vault",
        type=str,
        default="~/AI_Employee_Vault",
        help="Path to create the Obsidian vault (default: ~/AI_Employee_Vault)",
    )
    init_parser.set_defaults(func=cmd_init)

    # Scheduler command
    scheduler_parser = subparsers.add_parser(
        "scheduler",
        help="Manage scheduled tasks",
    )
    scheduler_parser.add_argument(
        "--vault",
        type=str,
        default="~/AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ~/AI_Employee_Vault)",
    )

    scheduler_subparsers = scheduler_parser.add_subparsers(
        title="scheduler commands",
        dest="scheduler_cmd",
        required=True,
    )

    # Scheduler list
    sched_list = scheduler_subparsers.add_parser("list", help="List all scheduled tasks")

    # Scheduler add
    sched_add = scheduler_subparsers.add_parser("add", help="Add a new scheduled task")
    sched_add.add_argument("--name", required=True, help="Task name")
    sched_add.add_argument("--schedule", required=True, help="Cron expression or ISO datetime")
    sched_add.add_argument("--type", default="custom", help="Task type (briefing, audit, custom)")
    sched_add.add_argument("--timezone", default="local", help="Timezone")
    sched_add.add_argument("--missed", default="run", help="Missed strategy (skip, run, queue)")

    # Scheduler remove
    sched_remove = scheduler_subparsers.add_parser("remove", help="Remove a scheduled task")
    sched_remove.add_argument("--id", required=True, help="Task ID to remove")

    # Scheduler run
    sched_run = scheduler_subparsers.add_parser("run", help="Run a task immediately")
    sched_run.add_argument("--id", required=True, help="Task ID to run")

    # Scheduler enable
    sched_enable = scheduler_subparsers.add_parser("enable", help="Enable a task")
    sched_enable.add_argument("--id", required=True, help="Task ID to enable")

    # Scheduler disable
    sched_disable = scheduler_subparsers.add_parser("disable", help="Disable a task")
    sched_disable.add_argument("--id", required=True, help="Task ID to disable")

    # Scheduler missed
    sched_missed = scheduler_subparsers.add_parser("missed", help="Show missed tasks")

    # Scheduler setup-defaults
    sched_defaults = scheduler_subparsers.add_parser("setup-defaults", help="Create default scheduled tasks")

    scheduler_parser.set_defaults(func=cmd_scheduler)

    return parser


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args()

    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
