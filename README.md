# AI Employee

Personal AI Employee - Autonomous Digital FTE using Claude Code and Obsidian.

## Overview

The AI Employee is a local-first automation system that:
- Monitors folders for new files (File System Watcher)
- Monitors Gmail for important emails (Gmail Watcher)
- Queues items for AI processing in `/Needs_Action`
- Uses Claude Code to process items according to your Company Handbook rules
- Provides a real-time Dashboard in Obsidian

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Initialize the vault structure
uv run ai-employee init --vault ~/AI_Employee_Vault

# 3. Start the file watcher
uv run ai-employee watch --vault ~/AI_Employee_Vault
```

## Installation

### Requirements

- Python 3.13+
- [UV package manager](https://github.com/astral-sh/uv)
- [Claude Code CLI](https://docs.anthropic.com/claude-code)
- [Obsidian](https://obsidian.md) (for viewing Dashboard)

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd personal-ai-employee

# Install with UV
uv sync

# For Gmail support, install optional dependencies
uv sync --extra gmail
```

## CLI Commands

### Initialize Vault

Create the folder structure for your AI Employee vault:

```bash
uv run ai-employee init --vault ~/AI_Employee_Vault
```

This creates:
- `Inbox/` - Raw incoming items
- `Needs_Action/` - Items queued for processing
- `Needs_Action/Email/` - Email action items
- `Done/` - Completed items
- `Drop/` - Drop files here to be processed
- `Quarantine/` - Items that failed processing
- `Logs/` - Activity and watcher logs
- `Dashboard.md` - Real-time status dashboard
- `Company_Handbook.md` - Processing rules

### Start File Watcher

Monitor the `/Drop` folder for new files:

```bash
uv run ai-employee watch --vault ~/AI_Employee_Vault --interval 60
```

Options:
- `--vault PATH` - Path to Obsidian vault (default: `~/AI_Employee_Vault`)
- `--interval SECONDS` - Keep-alive interval (default: 60)

### Start Gmail Watcher

Monitor Gmail for unread important emails:

```bash
uv run ai-employee watch-gmail --vault ~/AI_Employee_Vault --interval 120
```

Options:
- `--vault PATH` - Path to Obsidian vault
- `--credentials PATH` - Path to Gmail OAuth2 credentials.json
- `--interval SECONDS` - Poll interval (default: 120)

First-time setup requires OAuth2 authentication. See [Gmail Setup](#gmail-setup).

### Update Dashboard

Manually refresh the Dashboard.md:

```bash
uv run ai-employee dashboard --vault ~/AI_Employee_Vault
```

## Claude Code Skills

The AI Employee provides slash commands for use within Claude Code:

### `/process-inbox`

Process all pending items in `/Needs_Action` according to Company_Handbook.md rules.

```
/process-inbox
```

What it does:
1. Reads rules from Company_Handbook.md
2. Lists pending items in FIFO order
3. Processes each item according to type and rules
4. Moves completed items to `/Done`
5. Quarantines failed items
6. Updates Dashboard.md

### `/update-dashboard`

Refresh Dashboard.md with current system status.

```
/update-dashboard
```

What it does:
1. Counts pending items
2. Reads recent activity from logs
3. Checks watcher status
4. Generates updated Dashboard.md

### `/check-watcher-health`

Verify that watchers are running and healthy.

```
/check-watcher-health
```

What it does:
1. Checks for running watcher processes
2. Analyzes recent log entries
3. Reports status and any issues
4. Suggests remediation steps

## Claude Code Agents

Specialized agents for autonomous tasks:

### `inbox-processor`

Automatically processes the inbox when items need attention.

### `watcher-monitor`

Monitors watcher health and reports issues proactively.

## Vault Structure

```
AI_Employee_Vault/
├── Dashboard.md           # Real-time status (view in Obsidian)
├── Company_Handbook.md    # Your processing rules
├── Drop/                  # Drop files here to process
├── Inbox/                 # Raw incoming items
├── Needs_Action/          # Queued for AI processing
│   └── Email/             # Email action items
├── Done/                  # Completed items
├── Quarantine/            # Failed/problematic items
└── Logs/                  # Activity logs
    ├── claude_YYYY-MM-DD.log    # Processing activity
    └── watcher_YYYY-MM-DD.log   # Watcher events
```

## Company Handbook

Edit `Company_Handbook.md` to customize AI behavior:

```markdown
### Rule 1: Priority Keywords
- "urgent", "asap" → priority: urgent
- "important" → priority: high

### Rule 2: Email Handling
When processing emails:
- Summarize key points
- Identify action items
- Flag if response needed
```

Rules are applied in order. Add new rules as `### Rule N:` sections.

## Gmail Setup

1. Create a Google Cloud project
2. Enable Gmail API
3. Create OAuth2 credentials (Desktop app)
4. Download `credentials.json`
5. Run the watcher with credentials:
   ```bash
   uv run ai-employee watch-gmail --credentials ~/credentials.json
   ```
6. Complete OAuth flow in browser (first time only)

Token is saved to `~/.config/ai-employee/token.json`.

## Project Structure

```
src/ai_employee/
├── cli/            # Command line interface
│   └── main.py     # CLI entry point
├── models/         # Data models
│   ├── action_item.py    # ActionItem for processing
│   ├── activity_log.py   # Activity logging
│   ├── dashboard.py      # Dashboard state
│   └── watcher_event.py  # Watcher events
├── services/       # Business logic
│   ├── dashboard.py      # Dashboard generation
│   ├── handbook.py       # Handbook rule parsing
│   └── processor.py      # Item processing
├── utils/          # Utilities
│   ├── frontmatter.py    # YAML frontmatter parsing
│   └── jsonl_logger.py   # JSON lines logging
└── watchers/       # File system and Gmail watchers
    ├── base.py           # Abstract base watcher
    ├── filesystem.py     # File system watcher
    └── gmail.py          # Gmail watcher

.claude/
├── skills/         # Claude Code skills
│   ├── process-inbox/
│   ├── update-dashboard/
│   └── check-watcher/
└── agents/         # Claude Code agents
    ├── inbox-processor.md
    └── watcher-monitor.md
```

## Troubleshooting

### Watcher not detecting files
- Check that the watcher process is running: `ps aux | grep ai-employee`
- Verify vault path is correct
- Check `/Logs/watcher_*.log` for errors

### Files stuck in Drop folder
- Restart the watcher
- Check file permissions
- Look for errors in watcher logs

### Gmail authentication failing
- Delete `~/.config/ai-employee/token.json`
- Re-run with `--credentials` to re-authenticate

### High error rate
- Review `/Quarantine` folder
- Check `Company_Handbook.md` for conflicting rules
- Read activity logs for details

## Development

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=ai_employee

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
```

## License

MIT
