# Data Model: Bronze Tier Personal AI Employee

**Date**: 2026-02-03
**Feature**: 001-bronze-ai-employee

## Entity Relationship Overview

```
┌─────────────────┐     ┌─────────────────┐
│  Watcher Event  │────▶│   Action Item   │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Activity Log    │
                        │    Entry        │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Dashboard     │
                        └─────────────────┘
```

## Entities

### 1. Action Item

**Description**: A file or message requiring AI processing

**Storage**: Markdown file in `/Needs_Action/` folder with YAML frontmatter

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | enum | Yes | `file_drop` or `email` |
| source | enum | Yes | `filesystem` or `gmail` |
| original_name | string | Yes | Original filename or email subject |
| created | datetime | Yes | ISO 8601 timestamp when item was created |
| status | enum | Yes | `pending`, `processing`, `done`, `quarantined` |
| priority | enum | Yes | `low`, `normal`, `high`, `urgent` |
| file_size | integer | No | File size in bytes (filesystem only) |
| file_type | string | No | File extension (filesystem only) |
| from_address | string | No | Sender email (gmail only) |
| message_id | string | No | Gmail message ID (gmail only) |
| processed_at | datetime | No | When item was processed |
| error | string | No | Error message if quarantined |

**State Transitions**:
```
[Created] ──▶ pending ──▶ processing ──▶ done
                │                          │
                └──▶ quarantined ◀─────────┘
                      (on error)
```

**Validation Rules**:
- `created` must be valid ISO 8601
- `status` must be one of defined values
- `priority` defaults to `normal` if not specified
- `file_size` must be positive integer if present

---

### 2. Activity Log Entry

**Description**: A record of an AI action taken

**Storage**: Appended to `/Logs/claude_YYYY-MM-DD.log` (JSON lines format)

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | datetime | Yes | When action occurred |
| action_type | enum | Yes | `process`, `move`, `update`, `error` |
| item_id | string | Yes | Filename of item processed |
| outcome | enum | Yes | `success`, `failure`, `skipped` |
| duration_ms | integer | No | Processing time in milliseconds |
| details | string | No | Additional context or error message |

**Example**:
```json
{"timestamp": "2026-02-03T10:30:00Z", "action_type": "process", "item_id": "FILE_example.txt.md", "outcome": "success", "duration_ms": 1234}
```

---

### 3. Watcher Event

**Description**: A detection event from a watcher

**Storage**: Appended to `/Logs/watcher_YYYY-MM-DD.log` (JSON lines format)

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | datetime | Yes | When event occurred |
| source_type | enum | Yes | `filesystem` or `gmail` |
| event_type | enum | Yes | `created`, `modified`, `deleted`, `error` |
| identifier | string | Yes | File path or message ID |
| metadata | object | No | Additional event-specific data |

**Example**:
```json
{"timestamp": "2026-02-03T10:30:00Z", "source_type": "filesystem", "event_type": "created", "identifier": "/path/to/Drop/file.txt", "metadata": {"size": 1234}}
```

---

### 4. Handbook Rule

**Description**: A directive governing AI behavior

**Storage**: Within `Company_Handbook.md` as markdown sections

**Structure**:
```markdown
## Rules

### Rule 1: Priority Keywords
When processing items, check for these keywords and set priority:
- "urgent", "asap", "emergency" → priority: urgent
- "important", "priority" → priority: high

### Rule 2: Response Tone
Always be polite and professional in any generated responses.

### Rule 3: Approval Thresholds
Flag for manual review if:
- File size > 10MB
- Unknown file type
```

**Parsing**: Rules are extracted by section headers (### Rule N:)

---

### 5. Dashboard State

**Description**: Current system status displayed to user

**Storage**: `Dashboard.md` at vault root

**Sections**:

| Section | Content |
|---------|---------|
| Status | Watcher state, pending count, today's processed count |
| Recent Activity | Last 10 activity log entries as table |
| Warnings | Error alerts if threshold exceeded |

**Update Trigger**: After each item processed or on /update-dashboard command

---

## File Naming Conventions

| Entity | Location | Naming Pattern |
|--------|----------|----------------|
| Action Item (file) | `/Needs_Action/` | `FILE_{original_name}.md` |
| Action Item (email) | `/Needs_Action/Email/` | `EMAIL_{message_id}.md` |
| Processed Item | `/Done/` | Same name, moved |
| Quarantined Item | `/Quarantine/` | Same name, moved |
| Activity Log | `/Logs/` | `claude_YYYY-MM-DD.log` |
| Watcher Log | `/Logs/` | `watcher_YYYY-MM-DD.log` |

---

## Vault Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md              # System status (auto-updated)
├── Company_Handbook.md       # User-defined rules
├── Inbox/                    # Reserved for future use
├── Needs_Action/             # Pending items for processing
│   └── Email/                # Email-specific items
├── Done/                     # Successfully processed items
├── Drop/                     # Watcher monitors this folder
├── Quarantine/               # Failed/problematic items
└── Logs/                     # Activity and watcher logs
    ├── claude_2026-02-03.log
    └── watcher_2026-02-03.log
```
