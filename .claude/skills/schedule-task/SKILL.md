---
name: schedule-task
description: Configure recurring or one-time scheduled tasks using cron expressions. Use when user wants to schedule a task, set up recurring jobs, create automated routines, configure daily briefings, weekly reports, or any time-based automation.
---

# Schedule Task

Configure recurring or one-time scheduled tasks.

## Usage

```
/schedule-task <action> [options]
```

## Quick Start

```bash
# List all tasks
scripts/manage_schedules.py list

# Create daily briefing
scripts/manage_schedules.py create --name "Daily Briefing" --schedule "0 8 * * *" --action-type briefing

# Create one-time task
scripts/manage_schedules.py create --name "Quarterly Report" --schedule "2026-04-01T09:00:00" --action-type audit

# Disable/enable task
scripts/manage_schedules.py disable --id schedule_daily_briefing
scripts/manage_schedules.py enable --id schedule_daily_briefing

# Delete task
scripts/manage_schedules.py delete --id schedule_old_task
```

## Create Options

- `--name` (required): Task name
- `--schedule` (required): Cron expression or ISO datetime
- `--action-type` (required): briefing, audit, custom
- `--timezone` (optional): Timezone (default: local)
- `--missed` (optional): skip, run, queue (default: run)

## Cron Expression Format

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sun=0)
│ │ │ │ │
* * * * *
```

**Common Examples:**
- `0 8 * * *` - Daily 8:00 AM
- `0 21 * * 0` - Sunday 9:00 PM
- `0 9 * * 1-5` - Weekdays 9:00 AM
- `*/15 * * * *` - Every 15 minutes

## JSON Output

```bash
scripts/manage_schedules.py list --json
```

```json
{
  "success": true,
  "count": 2,
  "tasks": [
    {
      "id": "schedule_daily_briefing",
      "name": "Daily Briefing",
      "schedule": "0 8 * * *",
      "enabled": true
    }
  ]
}
```

## Action Types

- `briefing` - Generate daily/weekly briefing
- `audit` - Generate audit report
- `update_dashboard` - Refresh Dashboard.md
- `check_approvals` - Check expired approvals
- `custom` - Run custom script

## Missed Schedule Strategies

- `skip` - Don't run missed tasks
- `run` - Run immediately (default)
- `queue` - Add to queue
