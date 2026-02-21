# Personal AI Employee

Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

![AI Employee Mission Control](docs/images/dashboard.png)

A **Digital FTE (Full-Time Equivalent)** that proactively manages your personal and business affairs 24/7. Built with Claude Code as the reasoning engine and Obsidian as the knowledge base, it monitors Gmail, WhatsApp, and file systems, processes tasks autonomously, posts to social media, generates CEO briefings, manages invoices through Odoo, and keeps you in the loop for sensitive actions.

## Architecture

```text
External Sources            Perception Layer              Obsidian Vault (Local)
┌─────────────┐      ┌──────────────────────┐     ┌──────────────────────────┐
│ Gmail       │─────>│ Gmail Watcher        │────>│ /Needs_Action/Email/     │
│ WhatsApp    │─────>│ WhatsApp Watcher     │────>│ /Needs_Action/WhatsApp/  │
│ File System │─────>│ File System Watcher  │────>│ /Needs_Action/           │
│ LinkedIn    │─────>│ LinkedIn Watcher     │────>│ /Needs_Action/LinkedIn/  │
│ Meta/Twitter│─────>│ Meta/Twitter Watcher │────>│ /Social/                 │
└─────────────┘      └──────────────────────┘     └────────────┬─────────────┘
                                                               │
                     ┌──────────────────────┐                  │
                     │   Claude Code        │<─────────────────┘
                     │   Read → Think →     │
                     │   Plan → Act         │──────> /Plans/
                     └──────────┬───────────┘──────> /Pending_Approval/
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                   │
              ▼                 ▼                   ▼
     ┌────────────┐   ┌──────────────┐   ┌──────────────────┐
     │ Human-in-  │   │ MCP Servers  │   │ Ralph Wiggum     │
     │ the-Loop   │   │ Email, Odoo  │   │ Autonomous Loop  │
     │ /Approved/ │──>│ Meta, Twitter│   │ Multi-step Tasks │
     └────────────┘   └──────────────┘   └──────────────────┘
```

## Tier Overview

| Feature | Bronze | Silver | Gold |
|---------|--------|--------|------|
| File System Watcher | x | x | x |
| Gmail Watcher | x | x | x |
| Dashboard.md (Obsidian) | x | x | x |
| Item Processor + Handbook Rules | x | x | x |
| Web Dashboard (Mission Control) | | x | x |
| Human-in-the-Loop Approvals | | x | x |
| WhatsApp Monitoring | | x | x |
| LinkedIn Auto-Posting | | x | x |
| Plan.md Creation (Reasoning Loop) | | x | x |
| Email MCP Integration | | x | x |
| Cron-Based Scheduling | | x | x |
| Ralph Wiggum Autonomous Agent | | | x |
| CEO Briefing Generation | | | x |
| Meta (Facebook/Instagram) Posting | | | x |
| Twitter Posting | | | x |
| Odoo ERP Invoicing | | | x |
| Cross-Domain Search | | | x |
| Audit Logging | | | x |
| Error Recovery + Watchdog | | | x |

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/JahanzaibTayyab/personal-ai-employee.git
cd personal-ai-employee
uv sync

# 2. Initialize the vault
uv run ai-employee init --vault ~/AI_Employee_Vault

# 3. Start the file watcher (Bronze)
uv run ai-employee watch --vault ~/AI_Employee_Vault

# 4. Start the web dashboard (Silver+)
uv run ai-employee web --port 8000
# Open http://127.0.0.1:8000
```

## Installation

### Requirements

- **Python 3.13+**
- **[UV package manager](https://github.com/astral-sh/uv)** (replaces pip)
- **[Claude Code CLI](https://docs.anthropic.com/claude-code)** (reasoning engine)
- **[Obsidian](https://obsidian.md)** (for viewing Dashboard.md)
- **Node.js v24+** (for MCP servers, optional)

### Install by Tier

```bash
# Bronze: Core features
uv sync

# Silver: + Gmail, WhatsApp, LinkedIn, Dashboard
uv sync --extra gmail --extra dashboard

# Gold: Full installation (all integrations)
uv sync --all-extras
```

### Optional Dependency Groups

| Group | Packages | Tier |
|-------|----------|------|
| `gmail` | google-api-python-client, google-auth, google-auth-oauthlib | Bronze+ |
| `whatsapp` | playwright | Silver+ |
| `linkedin` | linkedin-api | Silver+ |
| `dashboard` | fastapi, uvicorn, jinja2, python-multipart | Silver+ |

## CLI Commands

### `init` - Initialize Vault

```bash
uv run ai-employee init --vault ~/AI_Employee_Vault
```

Creates the complete folder structure with `Dashboard.md`, `Company_Handbook.md`, and `Business_Goals.md`.

### `watch` - File System Watcher (Bronze)

Monitors the `/Drop` folder and moves new files to `/Needs_Action` for processing.

```bash
uv run ai-employee watch --vault ~/AI_Employee_Vault --interval 60
```

| Option | Default | Description |
|--------|---------|-------------|
| `--vault` | `~/AI_Employee_Vault` | Path to Obsidian vault |
| `--interval` | `60` | Keep-alive interval (seconds) |

### `watch-gmail` - Gmail Watcher (Bronze)

Monitors Gmail for unread important emails and creates action items.

```bash
uv run ai-employee watch-gmail --vault ~/AI_Employee_Vault --credentials ~/credentials.json --interval 120
```

| Option | Default | Description |
|--------|---------|-------------|
| `--vault` | `~/AI_Employee_Vault` | Path to Obsidian vault |
| `--credentials` | None | Path to Gmail OAuth2 credentials.json |
| `--interval` | `120` | Poll interval (seconds) |

See [Gmail Setup](#gmail-setup) for first-time OAuth2 configuration.

### `watch-approvals` - Approval Watcher (Silver)

Watches `/Pending_Approval` for approved/rejected items and triggers actions.

```bash
uv run ai-employee watch-approvals --vault ~/AI_Employee_Vault --interval 60
```

### `watch-whatsapp` - WhatsApp Watcher (Silver)

Monitors WhatsApp Web for messages containing keywords using Playwright.

```bash
uv run ai-employee watch-whatsapp --vault ~/AI_Employee_Vault --keywords "urgent,asap,invoice,payment,help,pricing"
```

### `dashboard` - Update Dashboard.md

Manually refreshes the Obsidian Dashboard.md with current status.

```bash
uv run ai-employee dashboard --vault ~/AI_Employee_Vault
```

### `web` - Web Dashboard (Silver+)

Starts the Mission Control web dashboard with full API.

```bash
uv run ai-employee web --port 8000
```

Open http://127.0.0.1:8000 in your browser. API docs at http://127.0.0.1:8000/docs.

**Dashboard Features:**
- **Overview Tab** - Metric cards, pending approvals, active plans, scheduled tasks, quick actions, system health, watcher status
- **Social Media Tab** - Meta (Facebook/Instagram) posts, tweets, LinkedIn posts
- **Operations Tab** - Ralph Wiggum tasks, CEO briefings, invoices, audit log, cross-domain search
- **Detail Modals** - Click any item for full details with actions (approve, reject, pause, resume, publish)

### `scheduler` - Manage Scheduled Tasks (Silver)

```bash
# Setup default daily briefing + weekly audit
uv run ai-employee scheduler --vault ~/AI_Employee_Vault setup-defaults

# List all scheduled tasks
uv run ai-employee scheduler --vault ~/AI_Employee_Vault list

# Add a custom scheduled task
uv run ai-employee scheduler --vault ~/AI_Employee_Vault add \
  --name "Daily Briefing" \
  --schedule "0 8 * * *" \
  --type briefing

# Run a task immediately
uv run ai-employee scheduler --vault ~/AI_Employee_Vault run --id schedule_daily_briefing

# Enable/disable tasks
uv run ai-employee scheduler --vault ~/AI_Employee_Vault enable --id schedule_weekly_audit
uv run ai-employee scheduler --vault ~/AI_Employee_Vault disable --id schedule_weekly_audit

# Show missed tasks
uv run ai-employee scheduler --vault ~/AI_Employee_Vault missed

# Remove a task
uv run ai-employee scheduler --vault ~/AI_Employee_Vault remove --id schedule_daily_briefing
```

**Task Types:** `briefing`, `audit`, `update_dashboard`, `check_approvals`, `custom`

**Cron Schedule Examples:**

| Schedule | Meaning |
|----------|---------|
| `0 8 * * *` | Every day at 8:00 AM |
| `0 21 * * 0` | Every Sunday at 9:00 PM |
| `*/30 * * * *` | Every 30 minutes |
| `0 9 * * 1` | Every Monday at 9:00 AM |

## Running 24/7

Your AI Employee is designed to run continuously. The watchers are daemon processes that monitor Gmail, WhatsApp, files, and approvals in real-time. Without a process manager, a single network blip or exception kills your watcher and your AI Employee goes "dead" until you manually restart it.

### Prerequisites

```bash
# Install PM2 (process manager)
npm install -g pm2

# Install all Python dependencies
uv sync --all-extras

# Initialize the vault (if not done already)
uv run ai-employee init --vault ~/AI_Employee_Vault
```

### Quick Start: One Command

The repo includes ready-to-use scripts and a PM2 ecosystem config:

```bash
# Start everything (all watchers + web dashboard)
./scripts/start.sh

# Start only Bronze tier (file + gmail watchers)
./scripts/start.sh --only bronze

# Start Silver tier (Bronze + approvals + whatsapp + dashboard)
./scripts/start.sh --only silver

# Start Gold tier (everything)
./scripts/start.sh --only gold

# Start just the web dashboard
./scripts/start.sh --only dashboard
```

### What Gets Started

| Process | Description | Tier |
|---------|-------------|------|
| `file-watcher` | Monitors `/Drop` folder for new files | Bronze |
| `gmail-watcher` | Polls Gmail for unread important emails (120s interval) | Bronze |
| `approval-watcher` | Watches `/Pending_Approval` for approved/rejected items | Silver |
| `whatsapp-watcher` | Monitors WhatsApp Web for keyword-matched messages | Silver |
| `web-dashboard` | Mission Control web UI at http://127.0.0.1:8000 | Silver+ |

### Managing Processes

```bash
# Check status of all processes
pm2 status

# Or use our status script (shows vault health too)
./scripts/status.sh

# View logs (all processes)
pm2 logs

# View logs for a specific process
pm2 logs gmail-watcher
pm2 logs web-dashboard

# Restart a single process
pm2 restart gmail-watcher

# Restart everything
pm2 restart all

# Stop everything
./scripts/stop.sh

# Stop a specific process
./scripts/stop.sh file-watcher

# Delete all PM2 processes entirely
pm2 delete all
```

### Survive Reboots

PM2 can generate a system startup script so your AI Employee starts automatically on boot:

```bash
# Save the current process list
pm2 save

# Generate startup script (follow the output instructions)
pm2 startup

# On macOS this generates a launchd plist
# On Linux this generates a systemd service
# It will print a command to run with sudo — copy and run it
```

After running `pm2 startup` and `pm2 save`, your watchers will automatically restart when your machine reboots.

### Configuration

The PM2 ecosystem config is at `ecosystem.config.cjs`. Override settings with environment variables:

```bash
# Custom vault path
export AI_VAULT=~/MyCustomVault

# Custom Gmail credentials path
export GMAIL_CREDENTIALS=~/my-credentials.json

# Custom web dashboard port
export AI_WEB_PORT=3000

# Then start
./scripts/start.sh
```

Or edit `ecosystem.config.cjs` directly to change vault paths, intervals, restart behavior, etc.

### PM2 Ecosystem Config Reference

The `ecosystem.config.cjs` configures each process with:

| Setting | Value | Purpose |
|---------|-------|---------|
| `autorestart` | `true` | Restart on crash |
| `restart_delay` | `5000-15000ms` | Wait before restart (prevents rapid loops) |
| `max_restarts` | `20-50` | Give up after N restarts |
| `min_uptime` | `10s` | Process must run 10s to count as "started" |

### Alternative: systemd (Linux Server / Cloud VM)

For production deployment on a Linux server or cloud VM:

```ini
# /etc/systemd/system/ai-employee.service
[Unit]
Description=AI Employee - All Watchers + Dashboard
After=network.target

[Service]
Type=forking
User=your-user
WorkingDirectory=/path/to/personal-ai-employee
ExecStart=/usr/local/bin/pm2 start ecosystem.config.cjs
ExecReload=/usr/local/bin/pm2 restart all
ExecStop=/usr/local/bin/pm2 stop all
PIDFile=/home/your-user/.pm2/pm2.pid
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ai-employee
sudo systemctl start ai-employee
sudo systemctl status ai-employee
journalctl -u ai-employee -f  # View logs
```

### Scheduled Tasks (cron integration)

The scheduler service manages recurring tasks like daily briefings and weekly audits:

```bash
# Create default scheduled tasks (daily briefing + weekly audit)
uv run ai-employee scheduler --vault ~/AI_Employee_Vault setup-defaults

# Verify they were created
uv run ai-employee scheduler --vault ~/AI_Employee_Vault list
# Output:
#   Daily Briefing (schedule_daily_briefing)  — 0 8 * * *    — Enabled
#   Weekly Audit (schedule_weekly_audit)       — 0 21 * * 0   — Enabled
```

To trigger scheduled tasks via system cron:

```bash
crontab -e

# Daily CEO briefing at 8 AM
0 8 * * * cd /path/to/personal-ai-employee && uv run ai-employee scheduler --vault ~/AI_Employee_Vault run --id schedule_daily_briefing >> ~/AI_Employee_Vault/Logs/cron.log 2>&1

# Weekly audit Sunday 9 PM
0 21 * * 0 cd /path/to/personal-ai-employee && uv run ai-employee scheduler --vault ~/AI_Employee_Vault run --id schedule_weekly_audit >> ~/AI_Employee_Vault/Logs/cron.log 2>&1
```

### Monitoring Health

Check system health at any time:

```bash
# Quick status check
./scripts/status.sh

# Web dashboard health endpoint
curl http://127.0.0.1:8000/api/health

# PM2 monitoring dashboard (interactive)
pm2 monit
```

The web dashboard also shows real-time watcher status, system health, and service availability at http://127.0.0.1:8000.

## Claude Code Skills

Slash commands for use within Claude Code sessions:

### Bronze Tier

| Skill | Description |
|-------|-------------|
| `/process-inbox` | Process all pending items in `/Needs_Action` according to Company_Handbook.md rules |
| `/update-dashboard` | Refresh Dashboard.md with current system status |
| `/check-watcher-health` | Verify watchers are running and report issues |

### Silver Tier

| Skill | Description |
|-------|-------------|
| `/send-email` | Draft and send emails with human-in-the-loop approval |
| `/post-linkedin` | Schedule LinkedIn posts with approval workflow |
| `/create-plan` | Generate Plan.md files with step-by-step breakdowns |
| `/approve-action` | List and manage pending approval requests |
| `/schedule-task` | Configure recurring or one-time scheduled tasks |

### Gold Tier

| Skill | Description |
|-------|-------------|
| `/generate-briefing` | Generate CEO briefing with revenue, bottlenecks, suggestions |
| `/post-twitter` | Create and publish tweets |
| `/post-facebook` | Create and publish Facebook posts |
| `/post-instagram` | Create and publish Instagram posts |
| `/odoo-invoice` | Create and manage invoices via Odoo ERP |
| `/ralph-loop` | Start Ralph Wiggum autonomous multi-step task execution |

## Claude Code Agents

Custom subagents for autonomous operations:

| Agent | Description |
|-------|-------------|
| `inbox-processor` | Automatically processes items in `/Needs_Action` following handbook rules |
| `watcher-monitor` | Monitors watcher health and reports issues proactively |

## Web Dashboard API Endpoints

All endpoints are accessible at `http://127.0.0.1:8000/api/`.

### Status and Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | System status (inbox, needs_action, done, quarantine counts + watcher states) |
| GET | `/api/health` | Service health (vault, odoo, meta, twitter, gmail) |
| GET | `/api/audit` | Recent audit log entries |
| GET | `/api/correlations/search?q=<query>` | Cross-domain search across vault |

### Approvals (Silver)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/approvals` | List pending approval requests |
| POST | `/api/approvals/{id}/approve` | Approve and execute an action |
| POST | `/api/approvals/{id}/reject` | Reject an action |

### Plans (Silver)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/plans` | List active plans |
| GET | `/api/plans/{plan_id}` | Get full plan details with step progress |
| POST | `/api/plans/create` | Create a new plan from objective |

### Schedules (Silver)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/schedules` | List all scheduled tasks |

### Email (Silver)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/email/send` | Create email (queued for approval) |

### LinkedIn (Silver)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/linkedin/post` | Create LinkedIn post (queued for approval) |

### Ralph Wiggum Tasks (Gold)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List all autonomous tasks |
| POST | `/api/tasks` | Create new autonomous task |
| POST | `/api/tasks/{id}/pause` | Pause a running task |
| POST | `/api/tasks/{id}/resume` | Resume a paused task |

### CEO Briefings (Gold)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/briefings` | List generated briefings |
| GET | `/api/briefings/{filename}` | Get full briefing markdown content |
| POST | `/api/briefings/generate` | Generate briefing for a date range |

### Social Media (Gold)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/social/meta` | List Meta (Facebook/Instagram) posts |
| POST | `/api/social/meta` | Create Meta post |
| POST | `/api/social/meta/{id}/publish` | Publish a draft Meta post |
| GET | `/api/social/twitter` | List tweets |
| POST | `/api/social/twitter` | Create tweet |
| POST | `/api/social/twitter/{id}/publish` | Publish a draft tweet |

### Invoices (Gold)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/invoices` | List invoices (Odoo integration) |
| POST | `/api/invoices` | Create invoice |

### Inbox Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/inbox/process` | Process pending items (accepts `max_items` parameter) |

## End-to-End Scenarios

### Scenario 1: Invoice Flow (WhatsApp to Email)

A client sends a WhatsApp message asking for an invoice. The AI Employee detects the request, generates the invoice, sends it via email, and logs the transaction.

**Step 1 - Detection:** WhatsApp Watcher detects keyword "invoice" in message from Client A. Creates `/Needs_Action/WhatsApp/WHATSAPP_client_a.md`.

**Step 2 - Reasoning:** Claude reads the file, identifies the client, calculates the amount from rates, and creates a plan at `/Plans/PLAN_invoice_client_a.md` with steps:
- Identify client: Client A (client_a@email.com)
- Calculate amount: $1,500 (from rates)
- Generate invoice in Odoo
- Send via email (REQUIRES APPROVAL)
- Log transaction

**Step 3 - Approval:** Claude creates `/Pending_Approval/EMAIL_invoice_client_a.md` with email details. The Approval Watcher monitors this folder. You review in the web dashboard and click "Approve".

**Step 4 - Action:** The system detects approval and sends the email via the Email MCP with the invoice attached.

**Step 5 - Completion:** Dashboard updated, files moved to `/Done/`, audit log entry created.

### Scenario 2: CEO Monday Morning Briefing

The scheduled task runs every week and generates a comprehensive business report.

**Trigger:** Cron fires `scheduler run --id schedule_weekly_audit` at Sunday 9 PM.

**Process:** The Briefing Service:
1. Reads `Business_Goals.md` for targets and metrics
2. Scans `/Done/` for completed tasks this week
3. Checks `/Accounting/invoices/` for revenue data (Odoo)
4. Analyzes social media performance (Meta, Twitter, LinkedIn)
5. Identifies bottlenecks (tasks that took too long)
6. Generates proactive suggestions (unused subscriptions, upcoming deadlines)

**Output:** `/Briefings/2026-02-21_Monday_Briefing.md` with:
- Executive Summary
- Revenue (this week, MTD, trend)
- Completed Tasks
- Bottlenecks table
- Proactive Suggestions (cost optimization, deadlines)

### Scenario 3: Social Media Automation

**LinkedIn:** Use `/post-linkedin` or the web dashboard Quick Actions to draft a post. It queues in `/Pending_Approval/`. After approval, it publishes via the LinkedIn API. The LinkedIn Engagement Watcher monitors for comments and sales leads.

**Meta (Facebook/Instagram):** Use `/post-facebook` or `/post-instagram`. Posts are created via the Meta Graph API. The Meta Engagement Watcher tracks likes, comments, and reach.

**Twitter:** Use `/post-twitter` to create tweets (280 char limit). The Twitter Mention Watcher monitors for replies and engagement.

### Scenario 4: Ralph Wiggum Autonomous Task

For complex multi-step tasks that require continuous iteration:

```bash
/ralph-loop "Process all inbox items and generate weekly summary for the board meeting"
```

The Ralph Wiggum pattern uses a Stop hook to keep Claude iterating:
1. Orchestrator creates task state file in `/Active_Tasks/`
2. Claude works on the task
3. Claude tries to exit
4. Stop hook checks: Is task complete?
   - YES: Allow exit
   - NO: Re-inject prompt, continue iteration
5. Task state shows progress (iteration count, status) in the web dashboard
6. Tasks can be paused/resumed from the dashboard

### Scenario 5: Email Triage

Gmail Watcher detects an important unread email:
1. Creates `/Needs_Action/Email/EMAIL_<id>.md` with sender, subject, snippet
2. `/process-inbox` applies Company_Handbook.md rules:
   - Keywords "urgent"/"asap" get priority: urgent
   - Summarizes key points
   - Identifies action items
   - If reply needed, drafts response via `/send-email` (requires approval)
3. Processed items move to `/Done/`
4. Dashboard.md updated with activity

## Vault Structure

```text
AI_Employee_Vault/
├── Dashboard.md                    # Real-time status (view in Obsidian)
├── Company_Handbook.md             # Processing rules ("Rules of Engagement")
├── Business_Goals.md               # Revenue targets, KPIs, project tracking
│
├── Drop/                           # Drop files here for automatic processing
├── Inbox/                          # Raw incoming items
├── Needs_Action/                   # Queued for AI processing
│   ├── Email/                      # Email action items
│   ├── WhatsApp/                   # WhatsApp action items (Silver)
│   └── LinkedIn/                   # LinkedIn engagement items (Silver)
├── Done/                           # Completed items
├── Quarantine/                     # Failed/problematic items
│
├── Pending_Approval/               # Awaiting human approval (Silver)
├── Approved/                       # Approved items (Silver)
├── Rejected/                       # Rejected items (Silver)
│
├── Plans/                          # Active Plan.md files (Silver)
├── Briefings/                      # Generated CEO briefings (Gold)
├── Schedules/                      # Schedule YAML configurations (Silver)
├── Active_Tasks/                   # Ralph Wiggum task states (Gold)
│
├── Social/                         # Social media content
│   ├── LinkedIn/posts/             # LinkedIn post drafts (Silver)
│   ├── Twitter/tweets/             # Tweet files (Gold)
│   └── Meta/posts/                 # Facebook/Instagram posts (Gold)
│
├── Accounting/invoices/            # Odoo invoices (Gold)
│
└── Logs/                           # Activity logs
    ├── claude_YYYY-MM-DD.log       # Processing activity
    ├── watcher_YYYY-MM-DD.log      # Watcher events
    ├── approval_YYYY-MM-DD.log     # Approval events (Silver)
    ├── linkedin_YYYY-MM-DD.log     # LinkedIn activity (Silver)
    └── scheduler_YYYY-MM-DD.log    # Scheduler activity (Silver)
```

## Company Handbook

Edit `Company_Handbook.md` to customize AI behavior. Rules are applied in order:

```markdown
### Rule 1: Priority Keywords
- "urgent", "asap" -> priority: urgent
- "important" -> priority: high

### Rule 2: Email Handling
When processing emails:
- Summarize key points
- Identify action items
- Flag if response needed

### Rule 3: Payment Approval
Any payment over $100 requires human approval.
Never auto-approve payments to new recipients.

### Rule 4: Social Media
- LinkedIn posts must be professional tone
- Tweets limited to 280 characters
- All social posts require approval before publishing
```

## Human-in-the-Loop Approval

Sensitive actions never execute automatically. The approval workflow:

1. **Claude detects sensitive action** (email to new contact, payment, social post)
2. **Creates approval file** in `/Pending_Approval/` with full details
3. **Approval Watcher** monitors the folder (or use the web dashboard)
4. **You review and approve/reject** - move file to `/Approved/` or `/Rejected/`, or click in dashboard
5. **Action executes** only after approval

**Permission Boundaries:**

| Action | Auto-Approve | Always Require Approval |
|--------|--------------|------------------------|
| Email replies | To known contacts | New contacts, bulk sends |
| Payments | < $50 recurring | All new payees, > $100 |
| Social media | Scheduled posts | Replies, DMs |
| File operations | Create, read | Delete, move outside vault |

## Gmail Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Gmail API**
4. Create **OAuth2 credentials** (Application type: Desktop app)
5. Download `credentials.json`
6. Run the watcher:
   ```bash
   uv run ai-employee watch-gmail --vault ~/AI_Employee_Vault --credentials ~/credentials.json
   ```
7. Complete OAuth flow in browser (first time only)

Token is saved to `~/.config/ai-employee/token.json` and refreshes automatically.

## Odoo ERP Setup (Gold)

For invoice management and accounting integration:

1. Install [Odoo Community Edition](https://www.odoo.com/documentation) (self-hosted or cloud)
2. Enable JSON-RPC API access
3. Configure environment variables:
   ```bash
   # .env
   ODOO_URL=http://localhost:8069
   ODOO_DB=your_database
   ODOO_USER=admin
   ODOO_PASSWORD=your_password
   ```
4. The Odoo MCP server connects via JSON-RPC for invoice CRUD operations

## Social Media Setup (Gold)

### Meta (Facebook/Instagram)

1. Create a [Meta Developer App](https://developers.facebook.com/)
2. Get a Page Access Token with `pages_manage_posts` permission
3. Configure:
   ```bash
   META_PAGE_ID=your_page_id
   META_ACCESS_TOKEN=your_token
   ```

### Twitter

1. Create a [Twitter Developer App](https://developer.twitter.com/)
2. Get API keys with tweet write permissions
3. Configure:
   ```bash
   TWITTER_API_KEY=your_key
   TWITTER_API_SECRET=your_secret
   TWITTER_ACCESS_TOKEN=your_token
   TWITTER_ACCESS_SECRET=your_token_secret
   ```

## Project Structure

```text
src/ai_employee/
├── cli/                    # Command line interface
│   └── main.py             # All CLI commands (watch, web, scheduler, etc.)
├── config.py               # VaultConfig - all vault paths
│
├── models/                 # Data models (dataclasses)
│   ├── action_item.py      # ActionItem, Priority, SourceType
│   ├── activity_log.py     # ActivityLogEntry
│   ├── approval_request.py # ApprovalRequest, ApprovalStatus (Silver)
│   ├── dashboard.py        # DashboardState
│   ├── watcher_event.py    # WatcherEvent
│   ├── whatsapp_message.py # WhatsAppMessage (Silver)
│   ├── linkedin_post.py    # LinkedInPost, LinkedInEngagement (Silver)
│   ├── plan.py             # Plan, PlanStep (Silver)
│   ├── scheduled_task.py   # ScheduledTask, TaskType (Silver)
│   ├── briefing.py         # CEOBriefing, Bottleneck, CostSuggestion (Gold)
│   ├── meta_post.py        # MetaPost, MetaEngagement (Gold)
│   ├── tweet.py            # Tweet, TweetEngagement (Gold)
│   ├── odoo_models.py      # OdooInvoice, OdooPayment (Gold)
│   ├── audit_entry.py      # AuditEntry (Gold)
│   ├── task_state.py       # TaskState for Ralph Wiggum (Gold)
│   ├── service_health.py   # ServiceHealth (Gold)
│   └── enums.py            # Shared enums (Gold)
│
├── services/               # Business logic
│   ├── processor.py        # ItemProcessor - process action items
│   ├── dashboard.py        # DashboardService - generate Dashboard.md
│   ├── handbook.py         # HandbookParser - parse rules
│   ├── approval.py         # ApprovalService (Silver)
│   ├── email.py            # EmailService - Gmail MCP (Silver)
│   ├── linkedin.py         # LinkedInService (Silver)
│   ├── planner.py          # PlannerService - Plan.md creation (Silver)
│   ├── scheduler.py        # SchedulerService - cron tasks (Silver)
│   ├── briefing.py         # BriefingService - CEO briefings (Gold)
│   ├── ralph_wiggum.py     # RalphWiggumService - autonomous loop (Gold)
│   ├── meta.py             # MetaService - FB/IG posting (Gold)
│   ├── twitter.py          # TwitterService (Gold)
│   ├── odoo.py             # OdooService - ERP invoicing (Gold)
│   ├── audit.py            # AuditService - audit logging (Gold)
│   ├── cross_domain.py     # CrossDomainService - search (Gold)
│   ├── error_recovery.py   # ErrorRecoveryService (Gold)
│   └── watchdog.py         # WatchdogService - health monitoring (Gold)
│
├── watchers/               # Background monitoring processes
│   ├── base.py             # BaseWatcher - abstract base class
│   ├── filesystem.py       # FileSystemWatcher (Bronze)
│   ├── gmail.py            # GmailWatcher (Bronze)
│   ├── approval.py         # ApprovalWatcher (Silver)
│   ├── whatsapp.py         # WhatsAppWatcher - Playwright (Silver)
│   ├── linkedin.py         # LinkedInEngagementWatcher (Silver)
│   ├── meta.py             # MetaEngagementWatcher (Gold)
│   └── twitter.py          # TwitterMentionWatcher (Gold)
│
├── dashboard/              # Web dashboard
│   ├── server.py           # FastAPI server + Bronze/Silver endpoints
│   ├── gold_routes.py      # Gold tier API endpoints
│   ├── templates/          # Jinja2 HTML templates
│   └── static/             # CSS + JS assets
│
├── mcp/                    # MCP integrations
│   ├── gmail_config.py     # Gmail OAuth2 + token management
│   ├── odoo_config.py      # Odoo ERP configuration
│   ├── calendar_config.py  # Calendar integration
│   └── browser_config.py   # Browser automation
│
└── utils/                  # Utilities
    ├── frontmatter.py      # YAML frontmatter parsing
    ├── jsonl_logger.py     # JSON lines structured logging
    └── correlation.py      # Cross-domain correlation
```

## Security

- **Never store credentials in the vault.** Use environment variables or a secrets manager.
- **All sensitive actions require approval.** The human-in-the-loop pattern prevents accidental payments, emails to wrong recipients, or unauthorized social posts.
- **Audit logging.** Every action is logged in `/Logs/` with timestamps, action type, approval status, and result.
- **DEV_MODE flag.** Prevents real external actions during development.
- **Credential rotation.** Rotate OAuth tokens and API keys monthly.

```bash
# .env - NEVER commit this file
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
ODOO_URL=http://localhost:8069
ODOO_DB=your_database
META_PAGE_ID=your_page_id
META_ACCESS_TOKEN=your_token
TWITTER_API_KEY=your_key
```

## Error Recovery

The system handles failures gracefully:

| Error Type | Examples | Recovery |
|------------|----------|----------|
| Transient | Network timeout, API rate limit | Exponential backoff retry |
| Authentication | Expired token, revoked access | Alert human, pause operations |
| Logic | Claude misinterprets message | Human review queue |
| Data | Corrupted file, missing field | Quarantine + alert |
| System | Process crash, disk full | Watchdog auto-restart |

When components fail:
- **Gmail API down:** Queue outgoing emails locally, process when restored
- **Banking API timeout:** Never retry payments automatically, require fresh approval
- **Claude unavailable:** Watchers continue collecting, queue grows for later
- **Vault locked:** Write to temporary folder, sync when available

## Troubleshooting

### Watcher not detecting files
- Check process is running: `ps aux | grep ai-employee`
- Verify vault path: `ls ~/AI_Employee_Vault/Drop/`
- Check logs: read `/Logs/watcher_*.log`

### Files stuck in Drop folder
- Restart the watcher: `pm2 restart file-watcher`
- Check file permissions
- Look for errors in watcher logs

### Gmail authentication failing
- Delete saved token: `rm ~/.config/ai-employee/token.json`
- Re-run with `--credentials` to re-authenticate
- Verify Gmail API is enabled in Google Cloud Console

### Watcher scripts stop running
- Use PM2 or supervisord for auto-restart (see [Running 24/7](#running-247))
- Check disk space: `df -h`
- Review logs for unhandled exceptions

### Web dashboard not loading
- Check server is running: `lsof -i :8000`
- Install dashboard extras: `uv sync --extra dashboard`
- Check `/tmp/web_dashboard.out` for errors

### High error rate
- Review `/Quarantine/` folder for failed items
- Check `Company_Handbook.md` for conflicting rules
- Read activity logs in `/Logs/`

## Development

```bash
# Run all tests (821 tests)
uv run pytest

# Run with coverage
uv run pytest --cov=ai_employee

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/

# Run specific test file
uv run pytest tests/unit/test_ralph_wiggum.py -v

# Run integration tests only
uv run pytest tests/integration/ -v
```

### Test Coverage by Tier

| Area | Tests | Tier |
|------|-------|------|
| Action Item, Config, Frontmatter, Handbook | 23 | Bronze |
| File System Watcher | 7 | Bronze |
| Gmail MCP | 32 | Bronze |
| Dashboard Server | 19 | Bronze/Silver |
| Approval Service + Workflow | 37 | Silver |
| Email Service | 25 | Silver |
| LinkedIn Post + Service | 43 | Silver |
| Plan + Planner Service | 41 | Silver |
| Scheduled Task + Scheduler | 43 | Silver |
| WhatsApp Message + Watcher | 36 | Silver |
| Skills Integration | 18 | Silver |
| Ralph Wiggum + Task State + Stop Hook | 81 | Gold |
| Briefing Model + Service | 46 | Gold |
| CEO Briefing Integration | 6 | Gold |
| Meta Post + Service | 47 | Gold |
| Tweet + Twitter Service | 40 | Gold |
| Odoo Models + Service | 42 | Gold |
| Audit Entry + Service | 34 | Gold |
| Cross-Domain Service | 23 | Gold |
| Dashboard Gold Endpoints | 28 | Gold |
| Error Recovery + Retry | 55 | Gold |
| Watchdog + Service Health | 26 | Gold |
| Redaction | 16 | Gold |
| Contract Tests (Meta, Odoo, Twitter) | 24 | Gold |
| Ralph Loop Integration | 15 | Gold |
| **Total** | **821** | |

## License

MIT
