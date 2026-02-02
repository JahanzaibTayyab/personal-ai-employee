# Personal AI Employee Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-03

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
    │   ├── action_item.py    # ActionItem for processing
    │   ├── activity_log.py   # Activity logging
    │   ├── dashboard.py      # Dashboard state
    │   └── watcher_event.py  # Watcher events
    ├── services/        # Business logic
    │   ├── dashboard.py      # Dashboard generation
    │   ├── handbook.py       # Handbook rule parsing
    │   └── processor.py      # Item processing
    ├── utils/           # Utilities
    │   ├── frontmatter.py    # YAML frontmatter parsing
    │   └── jsonl_logger.py   # JSON lines logging
    └── watchers/        # File and Gmail watchers
        ├── base.py           # Abstract base watcher
        ├── filesystem.py     # File system watcher
        └── gmail.py          # Gmail watcher

tests/
├── unit/                # Unit tests
└── integration/         # Integration tests

scripts/
└── init_vault.sh        # Vault initialization script

templates/
└── Company_Handbook.md  # Default handbook template

.claude/
├── skills/              # User-invocable skills (slash commands)
│   ├── process-inbox/
│   │   └── SKILL.md     # /process-inbox
│   ├── update-dashboard/
│   │   └── SKILL.md     # /update-dashboard
│   └── check-watcher/
│       └── SKILL.md     # /check-watcher-health
└── agents/              # Custom subagents
    ├── inbox-processor.md
    └── watcher-monitor.md
```

## Commands

```bash
# Initialize vault structure
uv run ai-employee init --vault ~/AI_Employee_Vault

# Start file watcher
uv run ai-employee watch --vault ~/AI_Employee_Vault

# Start Gmail watcher (requires OAuth setup)
uv run ai-employee watch-gmail --vault ~/AI_Employee_Vault --credentials ~/credentials.json

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
│   └── Email/             # Email action items
├── Done/                  # Completed items
├── Quarantine/            # Failed/problematic items
└── Logs/                  # Activity logs
    ├── claude_YYYY-MM-DD.log    # Processing activity
    └── watcher_YYYY-MM-DD.log   # Watcher events
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

## Recent Changes

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
