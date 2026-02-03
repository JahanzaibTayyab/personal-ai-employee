# Personal AI Employee Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-04

## Active Technologies

- **Python 3.13+** with UV package manager (src layout)
- **watchdog** - File system monitoring
- **pyyaml** - YAML frontmatter parsing
- **google-auth + google-api-python-client** - Gmail integration (optional)
- **pytest + pytest-cov** - Testing and coverage
- **mypy** - Static type checking
- **ruff** - Linting and formatting

## Project Structure

```text
pyproject.toml           # UV dependency management
src/
└── ai_employee/         # Main package
    ├── cli/             # CLI entry points
    │   └── main.py      # ai-employee command
    ├── config.py        # VaultConfig and Config classes
    ├── models/          # Data models
    │   ├── action_item.py       # ActionItem for processing
    │   ├── activity_log.py      # Activity logging
    │   ├── approval_request.py  # Approval workflow requests (Silver)
    │   ├── dashboard.py         # Dashboard state
    │   ├── linkedin_post.py     # LinkedIn posts and engagement (Silver)
    │   ├── plan.py              # Plan and PlanStep models (Silver)
    │   ├── scheduled_task.py    # Scheduled tasks (Silver)
    │   ├── watcher_event.py     # Watcher events
    │   └── whatsapp_message.py  # WhatsApp messages (Silver)
    ├── services/        # Business logic
    │   ├── approval.py       # Approval workflow service (Silver)
    │   ├── dashboard.py      # Dashboard generation
    │   ├── email.py          # Email drafting/sending (Silver)
    │   ├── handbook.py       # Handbook rule parsing
    │   ├── linkedin.py       # LinkedIn posting (Silver)
    │   ├── planner.py        # Plan.md creation (Silver)
    │   ├── processor.py      # Item processing
    │   └── scheduler.py      # Cron-based scheduling (Silver)
    ├── utils/           # Utilities
    │   ├── frontmatter.py    # YAML frontmatter parsing
    │   └── jsonl_logger.py   # JSON lines logging
    ├── mcp/             # MCP integrations (Silver)
    │   └── gmail_config.py   # Gmail MCP configuration
    └── watchers/        # File and Gmail watchers
        ├── base.py           # Abstract base watcher
        ├── approval.py       # Approval folder watcher (Silver)
        ├── filesystem.py     # File system watcher
        ├── gmail.py          # Gmail watcher
        ├── linkedin.py       # LinkedIn engagement watcher (Silver)
        └── whatsapp.py       # WhatsApp message watcher (Silver)

tests/
├── unit/                # Unit tests
└── integration/         # Integration tests

scripts/
└── init_vault.sh        # Vault initialization script

.claude/
├── skills/              # User-invocable skills (slash commands)
│   ├── process-inbox/       # /process-inbox
│   ├── update-dashboard/    # /update-dashboard
│   ├── check-watcher/       # /check-watcher-health
│   ├── post-linkedin/       # /post-linkedin (Silver)
│   ├── create-plan/         # /create-plan (Silver)
│   ├── send-email/          # /send-email (Silver)
│   ├── approve-action/      # /approve-action (Silver)
│   └── schedule-task/       # /schedule-task (Silver)
└── agents/              # Custom subagents
    ├── inbox-processor.md
    └── watcher-monitor.md
```

## Commands

```bash
# Initialize vault structure (includes Silver tier folders)
uv run ai-employee init --vault ~/AI_Employee_Vault

# Start file watcher
uv run ai-employee watch --vault ~/AI_Employee_Vault

# Start Gmail watcher (requires OAuth setup)
uv run ai-employee watch-gmail --vault ~/AI_Employee_Vault --credentials ~/credentials.json

# Start approval watcher (Silver tier)
uv run ai-employee watch-approvals --vault ~/AI_Employee_Vault

# Start WhatsApp watcher (Silver tier)
uv run ai-employee watch-whatsapp --vault ~/AI_Employee_Vault

# Manage scheduled tasks (Silver tier)
uv run ai-employee scheduler --vault ~/AI_Employee_Vault list
uv run ai-employee scheduler --vault ~/AI_Employee_Vault add --name "Daily Briefing" --schedule "0 8 * * *" --type briefing
uv run ai-employee scheduler --vault ~/AI_Employee_Vault run --id schedule_daily_briefing

# Update dashboard manually
uv run ai-employee dashboard --vault ~/AI_Employee_Vault

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=ai_employee

# Type checking
uv run mypy src/ai_employee

# Lint code
uv run ruff check src/ai_employee

# Add dependencies
uv add <package>
uv add --dev <package>
uv add <package> --optional gmail
```

**Note**: Never manually edit pyproject.toml for dependencies. Use `uv add` command.

## Code Style

- Python 3.13+: Follow PEP 8 conventions
- Use type hints for all function signatures
- Use dataclasses for data models
- Use pathlib for file operations
- Immutable patterns preferred (no mutation)
- Line length: 100 characters max

## Vault Structure

```text
AI_Employee_Vault/
├── Dashboard.md           # Real-time status (view in Obsidian)
├── Company_Handbook.md    # Processing rules
├── Drop/                  # Drop files here to process
├── Inbox/                 # Raw incoming items
├── Needs_Action/          # Queued for AI processing
│   ├── Email/             # Email action items
│   ├── WhatsApp/          # WhatsApp action items (Silver)
│   └── LinkedIn/          # LinkedIn engagement items (Silver)
├── Done/                  # Completed items
├── Quarantine/            # Failed/problematic items
├── Logs/                  # Activity logs
│   ├── claude_YYYY-MM-DD.log    # Processing activity
│   ├── watcher_YYYY-MM-DD.log   # Watcher events
│   ├── approval_YYYY-MM-DD.log  # Approval events (Silver)
│   ├── linkedin_YYYY-MM-DD.log  # LinkedIn activity (Silver)
│   └── scheduler_YYYY-MM-DD.log # Scheduler activity (Silver)
├── Pending_Approval/      # Items awaiting human approval (Silver)
├── Approved/              # Approved items (Silver)
├── Rejected/              # Rejected items (Silver)
├── Plans/                 # Active Plan.md files (Silver)
├── Social/                # Social media content (Silver)
│   └── LinkedIn/
│       ├── posts/         # LinkedIn post drafts
│       └── engagement.md  # Engagement log
├── Briefings/             # Generated briefings (Silver)
└── Schedules/             # Schedule configurations (Silver)
```

## Features

### 001-bronze-ai-employee (Complete)

Bronze Tier Personal AI Employee foundation:
- Obsidian vault as knowledge base (Dashboard.md, Company_Handbook.md)
- File System Watcher for automatic file detection from /Drop folder
- Gmail Watcher for unread important email monitoring (optional)
- Item Processor service for handling queued items
- Handbook Parser for rule-based processing
- Claude Code skills for modular AI functionality
- Custom agents for automated inbox processing and watcher monitoring

### 002-silver-ai-employee (Complete)

Silver Tier enhancements:
- **Human-in-the-Loop Approval Workflow**: Pending_Approval/Approved/Rejected folders for sensitive actions
- **WhatsApp Monitoring**: Playwright-based watcher with keyword detection for urgent messages
- **LinkedIn Auto-Posting**: Schedule posts with approval, track engagement, detect sales leads
- **Plan.md Creation**: Claude reasoning loop service for multi-step task breakdowns
- **Email MCP Integration**: Draft and send emails with approval workflow
- **Cron-Based Scheduling**: Daily briefings, weekly audits, custom scheduled tasks

## Silver Tier Skills

| Skill | Description |
|-------|-------------|
| `/post-linkedin` | Schedule LinkedIn posts with approval workflow |
| `/create-plan` | Generate Plan.md files with step-by-step breakdowns |
| `/send-email` | Draft emails requiring human approval before sending |
| `/approve-action` | List and manage pending approval requests |
| `/schedule-task` | Configure recurring or one-time scheduled tasks |

## Recent Changes

- 002-silver-ai-employee: Complete implementation of Silver tier
  - Approval workflow with ApprovalService and ApprovalWatcher
  - WhatsApp monitoring with keyword detection
  - LinkedIn service with post scheduling and engagement tracking
  - PlannerService for Plan.md creation
  - EmailService with Gmail MCP integration
  - SchedulerService with cron expressions and missed schedule handling
  - CLI commands: watch-approvals, watch-whatsapp, scheduler
  - Skills: /post-linkedin, /create-plan, /send-email, /approve-action, /schedule-task

- 001-bronze-ai-employee: Complete implementation of Bronze tier
  - File watcher with watchdog integration
  - Gmail watcher with OAuth2 authentication
  - Dashboard service with real-time status
  - Item processor with handbook rule integration
  - CLI commands: init, watch, watch-gmail, dashboard
  - Skills: /process-inbox, /update-dashboard, /check-watcher-health
  - Agents: inbox-processor, watcher-monitor

<!-- MANUAL ADDITIONS START -->
<!-- Add any manual guidelines below this line -->
<!-- MANUAL ADDITIONS END -->
