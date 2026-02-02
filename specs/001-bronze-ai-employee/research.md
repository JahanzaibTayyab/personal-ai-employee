# Research: Bronze Tier Personal AI Employee

**Date**: 2026-02-03
**Feature**: 001-bronze-ai-employee

## Research Questions

### 1. Python File Watching Libraries

**Question**: What is the best Python library for file system monitoring?

**Decision**: `watchdog` library

**Rationale**:
- Most mature and widely-used file monitoring library for Python
- Cross-platform support (macOS, Linux, Windows)
- Event-driven architecture (not polling-based, more efficient)
- Well-maintained with active community
- Simple API: Observer + EventHandler pattern

**Alternatives Considered**:
| Library | Pros | Cons | Rejected Because |
|---------|------|------|------------------|
| `watchfiles` | Fast, Rust-based | Less mature | Fewer examples, smaller community |
| `pyinotify` | Native Linux | Linux-only | No cross-platform support |
| `polling loop` | No dependencies | CPU intensive | Inefficient for continuous monitoring |

**Best Practices**:
- Use `Observer` with `FileSystemEventHandler` subclass
- Handle `on_created` events for new files
- Add debouncing to avoid duplicate events
- Run observer in separate thread

---

### 2. UV Package Manager with src Layout

**Question**: How to properly configure UV with src directory layout?

**Decision**: Use `uv init --package` for src layout with CLI entry points

**Source**: [UV Creating Projects](https://docs.astral.sh/uv/concepts/projects/init/)

**Rationale**:
- UV is the fastest Python package manager (10-100x faster than pip)
- Native support for `pyproject.toml`
- Handles virtual environments automatically
- `--package` flag creates src layout with CLI entry points

**Project Initialization**:
```bash
# Initialize project with src layout and CLI support
uv init --package ai-employee

# This creates:
# ai-employee/
# ├── pyproject.toml
# ├── README.md
# └── src/
#     └── ai_employee/
#         └── __init__.py
```

**Adding Dependencies** (never edit pyproject.toml directly):
```bash
# Add core dependencies (UV picks latest versions automatically)
uv add watchdog
uv add pyyaml

# Add optional Gmail dependencies
uv add google-auth --optional gmail
uv add google-api-python-client --optional gmail

# Add dev dependencies
uv add --dev pytest
uv add --dev pytest-cov
uv add --dev ruff
```

**UV Init Flags**:
| Flag | Build System | Structure | Use Case |
|------|--------------|-----------|----------|
| `--app` (default) | ❌ | Flat | Web apps, scripts |
| `--lib` | ✅ | src/ layout | Reusable libraries |
| `--package` | ✅ | src/ layout | CLI tools (our choice) |
| `--bare` | ❌ | Minimal | Custom projects |

**Best Practices**:
- Use `uv init --package <name>` to create project with src layout
- Use `uv add <package>` to add dependencies (auto-picks latest)
- Use `uv add --dev <package>` for dev dependencies
- Use `uv add --optional <group> <package>` for optional dependencies
- Use `uv sync` to install all dependencies
- Use `uv run` to execute scripts in the virtual environment
- Keep `uv.lock` in version control for reproducibility

---

### 3. Claude Code Skills (Slash Commands)

**Question**: How to implement Skills for Claude Code?

**Decision**: Create `SKILL.md` files in `.claude/skills/<skill-name>/` directories

**Rationale**:
- Skills are the modern approach (commands merged into skills)
- Support YAML frontmatter for configuration
- Can include supporting files in the skill directory
- Claude can auto-invoke based on description, or user can invoke with `/skill-name`

**Source**: [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)

**Skill Directory Structure**:
```
.claude/skills/
├── process-inbox/
│   ├── SKILL.md           # Main instructions (required)
│   └── examples/          # Optional supporting files
├── update-dashboard/
│   └── SKILL.md
└── check-watcher/
    └── SKILL.md
```

**SKILL.md Format**:
```yaml
---
name: process-inbox
description: Process all pending items in /Needs_Action folder. Use when user wants to process the inbox or after new items are detected.
disable-model-invocation: false
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

## Instructions

Process all files in the /Needs_Action folder according to Company_Handbook.md rules.

### Steps

1. Read Company_Handbook.md to understand processing rules
2. List all files in /Needs_Action folder
3. For each file:
   - Read the file content and frontmatter
   - Apply handbook rules to determine action
   - Process the item appropriately
   - Move to /Done with updated status
   - Log action to /Logs/claude_YYYY-MM-DD.log
4. Update Dashboard.md with new counts and activity

### Arguments

$ARGUMENTS - Optional filter for specific files to process
```

**Frontmatter Options**:

| Field | Description |
|-------|-------------|
| `name` | Slash command name (lowercase, hyphens) |
| `description` | When Claude should use this skill |
| `disable-model-invocation` | `true` = only user can invoke |
| `user-invocable` | `false` = only Claude can invoke |
| `allowed-tools` | Tools Claude can use without permission |
| `context` | `fork` to run in subagent context |
| `model` | Model to use (sonnet, opus, haiku) |

**Best Practices**:
- Keep SKILL.md under 500 lines
- Use `$ARGUMENTS` for dynamic input
- Reference vault paths explicitly
- Include error handling instructions
- Use `disable-model-invocation: true` for sensitive actions

---

### 3b. Claude Code Custom Subagents

**Question**: How to create custom agents for specialized tasks?

**Decision**: Create markdown files in `.claude/agents/` directory

**Source**: [Claude Code Subagents Documentation](https://code.claude.com/docs/en/sub-agents)

**Agent File Structure**:
```
.claude/agents/
├── inbox-processor.md    # Custom agent for inbox processing
└── watcher-monitor.md    # Custom agent for watcher health
```

**Agent File Format**:
```yaml
---
name: inbox-processor
description: Processes items in /Needs_Action following handbook rules. Use proactively when items need processing.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
permissionMode: default
skills:
  - process-inbox
---

You are an AI Employee inbox processor. Your job is to process all pending items in the /Needs_Action folder.

## Processing Rules

1. Always read Company_Handbook.md first
2. Process items in FIFO order (oldest first)
3. Log all actions to /Logs/
4. Update Dashboard.md after processing

## Output Format

For each item processed, report:
- Item name
- Action taken
- Result (success/failure)
- Time taken
```

**Agent Frontmatter Options**:

| Field | Description |
|-------|-------------|
| `name` | Unique identifier |
| `description` | When Claude should delegate to this agent |
| `tools` | Allowed tools (or inherits all) |
| `disallowedTools` | Tools to deny |
| `model` | sonnet, opus, haiku, or inherit |
| `permissionMode` | default, acceptEdits, dontAsk, bypassPermissions, plan |
| `skills` | Skills to preload into agent context |
| `hooks` | Lifecycle hooks for this agent |

**Built-in Agents**:
- `Explore` - Read-only codebase exploration (Haiku)
- `Plan` - Research for planning (inherits model)
- `general-purpose` - Full capability agent (inherits model)

**Best Practices**:
- Design focused agents for specific tasks
- Write detailed descriptions for auto-delegation
- Limit tool access for security
- Use `skills` field to preload relevant skills

---

### 4. Obsidian Markdown Frontmatter

**Question**: What format should action item metadata use?

**Decision**: YAML frontmatter at the top of markdown files

**Rationale**:
- Standard Obsidian convention
- Easily parsed with `pyyaml`
- Human-readable when viewing in Obsidian
- Supports structured metadata queries

**Schema**:
```yaml
---
type: file_drop | email
source: filesystem | gmail
original_name: "example.txt"
created: 2026-02-03T10:30:00Z
status: pending | processing | done | quarantined
priority: low | normal | high | urgent
file_size: 1234
file_type: ".txt"
---

## Content

[File content or description here]
```

**Best Practices**:
- Always include `type`, `source`, `created`, `status` fields
- Use ISO 8601 format for timestamps
- Keep frontmatter minimal (metadata only, not content)

---

### 5. Gmail API Integration (Optional)

**Question**: How to securely integrate Gmail API for the watcher?

**Decision**: OAuth2 with credentials stored outside vault

**Rationale**:
- Gmail API requires OAuth2 (no API keys)
- Credentials must be outside vault to avoid accidental sync
- Use environment variables for paths

**Setup Flow**:
1. Create Google Cloud project
2. Enable Gmail API
3. Create OAuth2 credentials (Desktop app type)
4. Download `credentials.json`
5. Store outside vault (e.g., `~/.config/ai-employee/`)
6. First run generates `token.json` (refresh token)

**Security Requirements**:
- Never commit credentials to git
- Use `GMAIL_CREDENTIALS_PATH` environment variable
- Implement token refresh handling
- Request minimal scopes: `gmail.readonly`

**Best Practices**:
- Track processed message IDs in a local file
- Poll every 2 minutes (respect rate limits)
- Handle token expiration gracefully

---

### 6. Dashboard.md Update Strategy

**Question**: How should Dashboard.md be updated?

**Decision**: Full file regeneration with templating

**Rationale**:
- Simpler than partial updates
- Ensures consistency
- Avoids parsing complexity
- Works well with Obsidian's file watching

**Template Structure**:
```markdown
# AI Employee Dashboard

**Last Updated**: {timestamp}

## Status

- **Watcher**: {running|stopped|unknown}
- **Pending Items**: {count}
- **Processed Today**: {count}

## Recent Activity

| Time | Action | Item | Result |
|------|--------|------|--------|
{activity_rows}

## Warnings

{warnings_if_any}

---
*Auto-generated by AI Employee*
```

**Best Practices**:
- Update after each item processed
- Include last 10 activity entries
- Show warnings if error threshold exceeded
- Add timestamp for staleness detection

---

## Resolved Clarifications

All technical decisions have been made. No outstanding NEEDS CLARIFICATION items.

## Dependencies Confirmed

| Dependency | Purpose | Install Command | Status |
|------------|---------|-----------------|--------|
| Python | Runtime (3.13+) | System install | Required |
| UV | Package management | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | Required |
| watchdog | File monitoring | `uv add watchdog` | Required |
| pyyaml | YAML parsing | `uv add pyyaml` | Required |
| google-auth | Gmail OAuth | `uv add google-auth --optional gmail` | Optional |
| google-api-python-client | Gmail API | `uv add google-api-python-client --optional gmail` | Optional |
| pytest | Testing | `uv add --dev pytest` | Dev |
| pytest-cov | Coverage | `uv add --dev pytest-cov` | Dev |
| ruff | Linting | `uv add --dev ruff` | Dev |

**Note**: UV automatically resolves and installs the latest compatible versions. Do not hardcode versions.
