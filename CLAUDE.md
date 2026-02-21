# Personal AI Employee Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-21

## Active Technologies

- **Python 3.13+** with UV package manager (src layout)
- **watchdog** - File system monitoring
- **pyyaml** - YAML frontmatter parsing
- **google-auth + google-api-python-client** - Gmail integration (optional)
- **odoorpc** - Odoo ERP JSON-RPC client (Gold)
- **facebook-sdk** - Meta/Facebook Graph API (Gold)
- **tweepy** - Twitter/X API v2 (Gold)
- **jinja2** - Template rendering for briefings (Gold)
- **pytest + pytest-cov** - Testing and coverage
- **mypy** - Static type checking
- **ruff** - Linting and formatting

## Project Structure

```text
pyproject.toml           # UV dependency management
src/
└── ai_employee/         # Main package
    ├── cli/             # CLI entry points
    │   ├── main.py          # ai-employee command
    │   └── ralph_stop_hook.py  # Ralph Wiggum stop hook (Gold)
    ├── config.py        # VaultConfig and Config classes
    ├── models/          # Data models
    │   ├── action_item.py       # ActionItem for processing
    │   ├── activity_log.py      # Activity logging
    │   ├── approval_request.py  # Approval workflow requests (Silver)
    │   ├── audit_entry.py       # Audit entry model (Gold)
    │   ├── briefing.py          # CEO Briefing models (Gold)
    │   ├── dashboard.py         # Dashboard state
    │   ├── enums.py             # Shared enums (Gold)
    │   ├── linkedin_post.py     # LinkedIn posts and engagement (Silver)
    │   ├── meta_post.py         # Meta/Facebook/Instagram posts (Gold)
    │   ├── odoo_models.py       # Odoo invoice/payment models (Gold)
    │   ├── plan.py              # Plan and PlanStep models (Silver)
    │   ├── scheduled_task.py    # Scheduled tasks (Silver)
    │   ├── service_health.py    # Service health tracking (Gold)
    │   ├── task_state.py        # Ralph Wiggum task state (Gold)
    │   ├── tweet.py             # Twitter/X tweet model (Gold)
    │   ├── watcher_event.py     # Watcher events
    │   └── whatsapp_message.py  # WhatsApp messages (Silver)
    ├── services/        # Business logic
    │   ├── approval.py       # Approval workflow service (Silver)
    │   ├── audit.py          # Audit logging service (Gold)
    │   ├── briefing.py       # CEO Briefing generation (Gold)
    │   ├── cross_domain.py   # Cross-domain integration (Gold)
    │   ├── dashboard.py      # Dashboard generation
    │   ├── email.py          # Email drafting/sending (Silver)
    │   ├── error_recovery.py # Error recovery & degraded mode (Gold)
    │   ├── handbook.py       # Handbook rule parsing
    │   ├── linkedin.py       # LinkedIn posting (Silver)
    │   ├── meta.py           # Meta/Facebook/Instagram service (Gold)
    │   ├── odoo.py           # Odoo ERP integration (Gold)
    │   ├── planner.py        # Plan.md creation (Silver)
    │   ├── processor.py      # Item processing
    │   ├── ralph_wiggum.py   # Ralph Wiggum autonomous loop (Gold)
    │   ├── scheduler.py      # Cron-based scheduling (Silver)
    │   ├── twitter.py        # Twitter/X service (Gold)
    │   └── watchdog.py       # Watcher auto-restart service (Gold)
    ├── templates/       # Jinja2 templates (Gold)
    │   └── ceo_briefing.md.j2  # CEO Briefing template
    ├── utils/           # Utilities
    │   ├── correlation.py   # Cross-domain correlation IDs (Gold)
    │   ├── frontmatter.py   # YAML frontmatter parsing
    │   ├── jsonl_logger.py  # JSON lines logging
    │   ├── redaction.py     # Sensitive data redaction (Gold)
    │   └── retry.py         # Exponential backoff retry (Gold)
    ├── mcp/             # MCP integrations (Silver)
    │   ├── gmail_config.py  # Gmail MCP configuration
    │   └── odoo_config.py   # Odoo MCP configuration (Gold)
    └── watchers/        # File and service watchers
        ├── base.py           # Abstract base watcher
        ├── approval.py       # Approval folder watcher (Silver)
        ├── filesystem.py     # File system watcher
        ├── gmail.py          # Gmail watcher
        ├── linkedin.py       # LinkedIn engagement watcher (Silver)
        ├── meta.py           # Meta engagement watcher (Gold)
        ├── twitter.py        # Twitter mention watcher (Gold)
        └── whatsapp.py       # WhatsApp message watcher (Silver)

tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
└── contract/            # Contract tests (Gold)

.claude/
├── hooks/               # Git/session hooks (Gold)
│   └── ralph-wiggum-stop.sh  # Ralph Wiggum stop hook
├── skills/              # User-invocable skills (slash commands)
│   ├── process-inbox/       # /process-inbox
│   ├── update-dashboard/    # /update-dashboard
│   ├── check-watcher/       # /check-watcher-health
│   ├── post-linkedin/       # /post-linkedin (Silver)
│   ├── create-plan/         # /create-plan (Silver)
│   ├── send-email/          # /send-email (Silver)
│   ├── approve-action/      # /approve-action (Silver)
│   ├── schedule-task/       # /schedule-task (Silver)
│   ├── ralph-loop/          # /ralph-loop (Gold)
│   ├── odoo-invoice/        # /odoo-invoice (Gold)
│   ├── generate-briefing/   # /generate-briefing (Gold)
│   ├── post-facebook/       # /post-facebook (Gold)
│   ├── post-instagram/      # /post-instagram (Gold)
│   └── post-twitter/        # /post-twitter (Gold)
└── agents/              # Custom subagents
    ├── inbox-processor.md
    ├── watcher-monitor.md
    └── business-auditor.md   # Weekly audit agent (Gold)
```

## Commands

```bash
# Initialize vault structure (includes Gold tier folders)
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
- Use dataclasses (frozen=True preferred) for data models
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
│   ├── LinkedIn/          # LinkedIn engagement items (Silver)
│   ├── Facebook/          # Facebook engagement items (Gold)
│   ├── Twitter/           # Twitter mention items (Gold)
│   └── Odoo/              # Odoo ERP items (Gold)
├── Done/                  # Completed items
├── Quarantine/            # Failed/problematic items
├── Logs/                  # Activity logs
│   ├── claude_YYYY-MM-DD.log    # Processing activity
│   ├── watcher_YYYY-MM-DD.log   # Watcher events
│   ├── approval_YYYY-MM-DD.log  # Approval events (Silver)
│   ├── linkedin_YYYY-MM-DD.log  # LinkedIn activity (Silver)
│   ├── scheduler_YYYY-MM-DD.log # Scheduler activity (Silver)
│   ├── audit_YYYY-MM-DD.log     # Audit trail (Gold)
│   ├── health_YYYY-MM-DD.log    # Service health (Gold)
│   └── queue/                    # Failed operation queue (Gold)
├── Pending_Approval/      # Items awaiting human approval (Silver)
├── Approved/              # Approved items (Silver)
├── Rejected/              # Rejected items (Silver)
├── Plans/                 # Active Plan.md files (Silver)
├── Active_Tasks/          # Ralph Wiggum task states (Gold)
├── Social/                # Social media content
│   ├── LinkedIn/
│   │   ├── posts/         # LinkedIn post drafts
│   │   └── engagement.md  # Engagement log
│   ├── Meta/              # Meta/Facebook/Instagram (Gold)
│   │   └── posts/         # Meta post drafts
│   └── Twitter/           # Twitter/X (Gold)
│       └── tweets/        # Tweet drafts
├── Accounting/            # Odoo ERP data (Gold)
│   ├── Invoices/          # Invoice records
│   ├── Payments/          # Payment records
│   └── Transactions/      # Transaction log
├── Correlations/          # Cross-domain correlation data (Gold)
├── Briefings/             # Generated briefings (Silver/Gold)
├── Schedules/             # Schedule configurations (Silver)
├── Archive/               # Archived items (Gold)
└── Business_Goals/        # Business goals & KPIs (Gold)
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

### 003-gold-ai-employee (Complete)

Gold Tier autonomous operations:
- **Ralph Wiggum Autonomous Loop**: Multi-step task execution with pause/resume, max 50 iterations, stop hook
- **Odoo ERP Integration**: Invoice/payment management, revenue reporting, offline queue, customer CRUD
- **CEO Weekly Briefing**: Jinja2-templated reports with revenue, bottlenecks, cost suggestions, social summary
- **Meta/Facebook/Instagram**: Post scheduling, publishing via Graph API, engagement tracking, business keyword detection
- **Twitter/X Integration**: Tweet/thread publishing via API v2, mention monitoring, engagement tracking
- **Error Recovery & Watchdog**: Service health tracking, exponential backoff retry, degraded mode, auto-restart
- **Cross-Domain Integration**: Correlation IDs, unified search across 14 vault domains, relationship graph
- **Enhanced Audit Logging**: JSONL audit trail, retention management, archival, sensitive data redaction

## Skills

| Skill | Tier | Description |
|-------|------|-------------|
| `/process-inbox` | Bronze | Process pending items in /Needs_Action |
| `/update-dashboard` | Bronze | Refresh Dashboard.md status |
| `/check-watcher` | Bronze | Verify watcher health |
| `/post-linkedin` | Silver | Schedule LinkedIn posts with approval |
| `/create-plan` | Silver | Generate Plan.md for multi-step tasks |
| `/send-email` | Silver | Draft emails with approval workflow |
| `/approve-action` | Silver | Manage pending approvals |
| `/schedule-task` | Silver | Configure scheduled tasks |
| `/ralph-loop` | Gold | Start Ralph Wiggum autonomous loop |
| `/odoo-invoice` | Gold | Create/manage Odoo invoices |
| `/generate-briefing` | Gold | Generate CEO weekly briefing |
| `/post-facebook` | Gold | Schedule Facebook posts |
| `/post-instagram` | Gold | Schedule Instagram posts |
| `/post-twitter` | Gold | Schedule tweets and threads |

## Recent Changes

- 003-gold-ai-employee: Complete implementation of Gold tier
  - Ralph Wiggum autonomous loop with TaskState, stop hook, pause/resume
  - Odoo ERP integration with OdooService, OdooMCPConfig, invoice/payment models
  - CEO Briefing with BriefingService, Jinja2 templates, revenue/bottleneck analysis
  - Meta/Facebook/Instagram with MetaService, MetaEngagementWatcher, Graph API
  - Twitter/X with TwitterService, TwitterMentionWatcher, API v2
  - Error Recovery with ErrorRecoveryService, WatchdogService, ServiceHealth
  - Cross-Domain with CrossDomainService, CorrelationContext, unified search
  - Audit logging with AuditService, AuditEntry, retention/archival
  - Gold tier enums: TaskStatus, InvoiceStatus, PaymentStatus, PostStatus, HealthStatus, ErrorCategory
  - Utilities: exponential backoff retry, correlation IDs, sensitive data redaction
  - Skills: /ralph-loop, /odoo-invoice, /generate-briefing, /post-facebook, /post-instagram, /post-twitter
  - Agents: business-auditor

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
