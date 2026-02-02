# Implementation Plan: Bronze Tier Personal AI Employee

**Branch**: `001-bronze-ai-employee` | **Date**: 2026-02-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bronze-ai-employee/spec.md`

## Summary

Build the foundational layer for an autonomous Personal AI Employee system. The Bronze tier establishes:
1. **Obsidian Vault** as the knowledge base and dashboard (Dashboard.md, Company_Handbook.md)
2. **Python File System Watcher** to detect and queue files for AI processing
3. **Claude Code Integration** to read/write vault files and process action items
4. **Agent Skills** (slash commands) for modular AI functionality

Technical approach: Local-first architecture using Python (UV + src layout) for watchers, Obsidian for the GUI/memory layer, and Claude Code Agent Skills for AI reasoning and actions.

## Technical Context

**Language/Version**: Python 3.13+
**Package Manager**: UV with `uv init --package` for src layout (`src/ai_employee/`)
**Primary Dependencies**:
- `uv add watchdog` - file monitoring
- `uv add pyyaml` - frontmatter parsing
- `uv add google-auth google-api-python-client --optional gmail` - optional Gmail
**Storage**: Local filesystem (Obsidian vault as Markdown files)
**Testing**: `uv add --dev pytest pytest-cov`
**Target Platform**: macOS/Linux desktop (local execution)
**Project Type**: Single Python project with CLI entry points + Claude Code Agent Skills
**Performance Goals**: File detection within 60 seconds, process 50+ items/day
**Constraints**: Must run continuously for 24+ hours without crashing, <100MB memory footprint
**Scale/Scope**: Single user, single vault, 1 watcher at a time

**Note**: UV automatically resolves latest compatible versions. Never hardcode versions.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is in template state (not yet customized for this project). Applying standard best practices:

| Gate | Status | Notes |
|------|--------|-------|
| Test-First | PASS | Will use pytest, TDD approach |
| Simplicity | PASS | Single project, minimal dependencies |
| Library-First | PASS | Watcher is a standalone library with CLI |
| Observability | PASS | All actions logged to /Logs/ folder |

No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-bronze-ai-employee/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (file schemas)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# Python project with UV + src layout
pyproject.toml           # UV dependency management
src/
└── ai_employee/
    ├── __init__.py
    ├── watchers/
    │   ├── __init__.py
    │   ├── base.py          # BaseWatcher abstract class
    │   ├── filesystem.py    # File System Watcher
    │   └── gmail.py         # Gmail Watcher (optional)
    ├── models/
    │   ├── __init__.py
    │   ├── action_item.py   # Action Item entity
    │   └── activity_log.py  # Activity Log Entry entity
    ├── services/
    │   ├── __init__.py
    │   ├── dashboard.py     # Dashboard update service
    │   └── processor.py     # Item processing orchestrator
    └── cli/
        ├── __init__.py
        └── main.py          # CLI entry point for watchers

tests/
├── __init__.py
├── unit/
│   ├── test_watchers.py
│   ├── test_models.py
│   └── test_services.py
└── integration/
    └── test_vault_operations.py

# Obsidian Vault (created at runtime, not in repo)
AI_Employee_Vault/       # User creates this
├── Dashboard.md
├── Company_Handbook.md
├── Inbox/
├── Needs_Action/
├── Done/
├── Drop/
├── Quarantine/
└── Logs/

# Claude Code Skills and Agents
.claude/
├── skills/                          # User-invocable skills (slash commands)
│   ├── process-inbox/
│   │   └── SKILL.md                 # /process-inbox skill
│   ├── update-dashboard/
│   │   └── SKILL.md                 # /update-dashboard skill
│   └── check-watcher/
│       └── SKILL.md                 # /check-watcher-health skill
└── agents/                          # Custom subagents for task delegation
    ├── inbox-processor.md           # Specialized agent for inbox processing
    └── watcher-monitor.md           # Specialized agent for watcher health
```

**Structure Decision**: Single Python project with src layout for proper packaging. Obsidian vault is created by user (not in repo) to maintain privacy. Skills use the new `.claude/skills/<skill-name>/SKILL.md` format with YAML frontmatter. Custom agents live in `.claude/agents/` for task-specific delegation.

## Complexity Tracking

No violations requiring justification. The architecture is intentionally simple:
- Single Python package
- File-based communication (no databases, no message queues)
- Local execution only (no cloud dependencies)
