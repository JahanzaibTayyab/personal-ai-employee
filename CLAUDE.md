# Personal AI Employee Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-03

## Active Technologies

- **Python 3.13+** with UV package manager (src layout)
- **watchdog** - File system monitoring
- **pyyaml** - YAML frontmatter parsing
- **google-auth + google-api-python-client** - Gmail integration (optional)
- **pytest + pytest-cov** - Testing and coverage

## Project Structure

```text
pyproject.toml           # UV dependency management
src/
└── ai_employee/         # Main package
    ├── watchers/        # File and Gmail watchers
    ├── models/          # Data models
    ├── services/        # Dashboard, processor services
    └── cli/             # CLI entry points

tests/
├── unit/                # Unit tests
└── integration/         # Integration tests

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
# Initialize new project with src layout
uv init --package ai-employee

# Add dependencies (UV picks latest versions)
uv add <package>
uv add --dev <package>
uv add <package> --optional <group>

# Sync all dependencies
uv sync

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=ai_employee

# Lint code
uv run ruff check .

# Start file watcher
uv run ai-employee watch --vault ~/AI_Employee_Vault
```

**Note**: Never manually edit pyproject.toml for dependencies. Use `uv add` command.

## Code Style

- Python 3.13+: Follow PEP 8 conventions
- Use type hints for all function signatures
- Use dataclasses for data models
- Use pathlib for file operations
- Immutable patterns preferred (no mutation)

## Features

### 001-bronze-ai-employee (Current)

Bronze Tier Personal AI Employee foundation:
- Obsidian vault as knowledge base (Dashboard.md, Company_Handbook.md)
- File System Watcher for automatic file detection
- Claude Code integration for AI processing
- Agent Skills for modular functionality

## Recent Changes

- 001-bronze-ai-employee: Initial feature branch for Bronze tier implementation

<!-- MANUAL ADDITIONS START -->
<!-- Add any manual guidelines below this line -->
<!-- MANUAL ADDITIONS END -->
