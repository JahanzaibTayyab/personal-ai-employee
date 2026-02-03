# Silver Tier - Data Model

**Created**: 2026-02-03 | **Plan**: [plan.md](./plan.md)

## Entity Relationship Diagram

```
┌─────────────────────┐     ┌─────────────────────┐
│   ApprovalRequest   │     │        Plan         │
├─────────────────────┤     ├─────────────────────┤
│ id: str             │     │ id: str             │
│ category: enum      │────▶│ objective: str      │
│ payload: dict       │     │ status: enum        │
│ status: enum        │     │ created_at: datetime│
│ created_at: datetime│     │ completed_at: opt   │
│ expires_at: datetime│     └─────────┬───────────┘
│ executed_at: opt    │               │ 1:N
└─────────────────────┘               ▼
                              ┌─────────────────────┐
                              │      PlanStep       │
                              ├─────────────────────┤
                              │ id: str             │
                              │ plan_id: str        │
                              │ order: int          │
                              │ description: str    │
                              │ status: enum        │
                              │ requires_approval   │
                              │ dependencies: list  │
                              └─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│   WhatsAppMessage   │     │   LinkedInPost      │
├─────────────────────┤     ├─────────────────────┤
│ id: str             │     │ id: str             │
│ sender: str         │     │ content: str        │
│ content: str        │     │ status: enum        │
│ timestamp: datetime │     │ scheduled_at: opt   │
│ keywords: list[str] │     │ posted_at: opt      │
│ action_status: enum │     │ engagement: dict    │
└─────────────────────┘     └─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│ LinkedInEngagement  │     │   ScheduledTask     │
├─────────────────────┤     ├─────────────────────┤
│ id: str             │     │ id: str             │
│ post_id: str        │     │ name: str           │
│ type: enum          │     │ schedule: str (cron)│
│ author: str         │     │ action: dict        │
│ content: str        │     │ enabled: bool       │
│ timestamp: datetime │     │ last_run: opt       │
│ requires_followup   │     │ next_run: opt       │
└─────────────────────┘     │ missed_strategy     │
                            └─────────────────────┘
```

---

## Entity Definitions

### ApprovalRequest

Represents an action awaiting human approval. Stored as markdown file in `/Pending_Approval/`.

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

class ApprovalCategory(str, Enum):
    """Category of approval request (FR-005)."""
    EMAIL = "email"
    SOCIAL_POST = "social_post"
    PAYMENT = "payment"
    FILE_OPERATION = "file_operation"
    CUSTOM = "custom"

class ApprovalStatus(str, Enum):
    """Status of approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"

@dataclass
class ApprovalRequest:
    """An action awaiting human approval (FR-001 to FR-005)."""

    id: str
    category: ApprovalCategory
    payload: dict[str, Any]  # Action-specific data
    created_at: datetime
    expires_at: datetime  # Default: 24 hours from created_at (FR-004)
    status: ApprovalStatus = ApprovalStatus.PENDING
    executed_at: datetime | None = None
    error: str | None = None

    # Validation: expires_at must be after created_at
    # State transitions: PENDING → APPROVED/REJECTED/EXPIRED → EXECUTED
```

**Frontmatter Schema:**
```yaml
---
id: "approval_20260203_143022_abc123"
category: "email"
status: "pending"
created_at: "2026-02-03T14:30:22"
expires_at: "2026-02-04T14:30:22"
payload:
  to: "client@example.com"
  subject: "Meeting Follow-up"
  body: "..."
  attachments: []
---

## Email Approval Request

**To**: client@example.com
**Subject**: Meeting Follow-up

### Body
...
```

---

### Plan

Represents a multi-step task breakdown created by the reasoning loop. Stored in `/Plans/`.

```python
class PlanStatus(str, Enum):
    """Status of a plan (FR-018)."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"  # Waiting for approval or failed step

@dataclass
class Plan:
    """Multi-step task breakdown (FR-016 to FR-020)."""

    id: str
    objective: str
    steps: list["PlanStep"] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    completion_summary: str | None = None

    # Validation: Must have at least one step
    # Contains: numbered steps, dependencies, approval requirements (FR-017)
```

---

### PlanStep

Individual step within a plan.

```python
class StepStatus(str, Enum):
    """Status of a plan step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    AWAITING_APPROVAL = "awaiting_approval"

@dataclass
class PlanStep:
    """Individual step in a plan (FR-017)."""

    id: str
    plan_id: str
    order: int  # 1-indexed step number
    description: str
    status: StepStatus = StepStatus.PENDING
    requires_approval: bool = False
    dependencies: list[str] = field(default_factory=list)  # Step IDs
    approval_request_id: str | None = None  # Links to ApprovalRequest if needed
    error: str | None = None
    completed_at: datetime | None = None
```

**Plan.md File Structure:**
```markdown
---
id: "plan_20260203_091500_xyz789"
objective: "Send weekly newsletter to subscribers"
status: "in_progress"
created_at: "2026-02-03T09:15:00"
---

# Plan: Send weekly newsletter to subscribers

## Objective
Send the weekly newsletter to all active subscribers.

## Steps

### Step 1: Gather newsletter content ✅
- **Status**: completed
- **Requires Approval**: No
- **Completed**: 2026-02-03T09:16:00

### Step 2: Draft email template ✅
- **Status**: completed
- **Requires Approval**: No
- **Dependencies**: Step 1

### Step 3: Send newsletter ⏳
- **Status**: awaiting_approval
- **Requires Approval**: Yes
- **Dependencies**: Step 2
- **Approval**: approval_20260203_091700_def456

## Success Criteria
- All active subscribers receive the newsletter
- Open rate tracked in engagement metrics
```

---

### WhatsAppMessage

Detected urgent message from WhatsApp watcher. Stored in `/Needs_Action/WhatsApp/`.

```python
class WhatsAppActionStatus(str, Enum):
    """Processing status for WhatsApp messages."""
    NEW = "new"
    REVIEWED = "reviewed"
    RESPONDED = "responded"
    ARCHIVED = "archived"

@dataclass
class WhatsAppMessage:
    """Detected urgent WhatsApp message (FR-006 to FR-010)."""

    id: str
    sender: str  # Sender name or phone number
    content: str
    timestamp: datetime
    keywords: list[str]  # Matched keywords (FR-007)
    action_status: WhatsAppActionStatus = WhatsAppActionStatus.NEW
    chat_name: str | None = None  # Group name if applicable
    phone_number: str | None = None

    # Keywords detected from configurable list (FR-007):
    # urgent, asap, invoice, payment, help, pricing
```

**Frontmatter Schema:**
```yaml
---
id: "whatsapp_20260203_143022"
sender: "John Client"
phone_number: "+1234567890"
timestamp: "2026-02-03T14:30:22"
keywords: ["urgent", "payment"]
action_status: "new"
---

## WhatsApp Message

**From**: John Client (+1234567890)
**Time**: 2026-02-03 14:30:22
**Keywords**: urgent, payment

### Message
Hi, this is urgent! I need help with the payment for invoice #1234.
```

---

### LinkedInPost

Scheduled or posted LinkedIn content. Stored in `/Social/LinkedIn/posts/`.

```python
class LinkedInPostStatus(str, Enum):
    """Status of LinkedIn post."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    POSTED = "posted"
    FAILED = "failed"

@dataclass
class LinkedInPost:
    """LinkedIn post content (FR-021 to FR-025)."""

    id: str
    content: str
    status: LinkedInPostStatus = LinkedInPostStatus.DRAFT
    scheduled_at: datetime | None = None
    posted_at: datetime | None = None
    approval_request_id: str | None = None
    linkedin_post_id: str | None = None  # ID from LinkedIn API after posting
    engagement: dict[str, int] = field(default_factory=lambda: {
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "impressions": 0
    })
    error: str | None = None

    # Rate limit: max 25 posts per day (FR-025)
```

---

### LinkedInEngagement

Engagement activity on LinkedIn posts.

```python
class EngagementType(str, Enum):
    """Type of LinkedIn engagement."""
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    MENTION = "mention"

@dataclass
class LinkedInEngagement:
    """LinkedIn engagement activity (FR-022 to FR-024)."""

    id: str
    post_id: str
    engagement_type: EngagementType
    author: str  # Name of person who engaged
    content: str | None = None  # Comment content if applicable
    timestamp: datetime = field(default_factory=datetime.now)
    requires_followup: bool = False  # True if matches keywords (FR-023)
    followup_keywords: list[str] = field(default_factory=list)

    # Keywords for followup detection (FR-023):
    # inquiry, interested, pricing, contact, demo
```

---

### ScheduledTask

Recurring or one-time scheduled operation. Stored in `/Schedules/`.

```python
class MissedStrategy(str, Enum):
    """How to handle missed schedules (FR-029)."""
    SKIP = "skip"
    RUN_IMMEDIATELY = "run_immediately"
    QUEUE = "queue"

@dataclass
class ScheduledTask:
    """Scheduled recurring or one-time task (FR-026 to FR-030)."""

    id: str
    name: str
    schedule: str  # Cron expression (FR-026) or ISO datetime for one-time (FR-027)
    action: dict[str, Any]  # Action configuration
    enabled: bool = True
    timezone: str = "local"  # User's timezone (FR-030)
    last_run: datetime | None = None
    next_run: datetime | None = None
    missed_strategy: MissedStrategy = MissedStrategy.RUN_IMMEDIATELY
    last_result: str | None = None
    error: str | None = None

    # Schedule examples:
    # - "0 8 * * *" = Daily at 8:00 AM
    # - "0 21 * * 0" = Weekly Sunday 9:00 PM
    # - "2026-02-10T15:00:00" = One-time at specific datetime
```

**Frontmatter Schema:**
```yaml
---
id: "schedule_daily_briefing"
name: "Daily Briefing"
schedule: "0 8 * * *"
timezone: "America/New_York"
enabled: true
missed_strategy: "run_immediately"
last_run: "2026-02-03T08:00:15"
next_run: "2026-02-04T08:00:00"
---

## Daily Briefing

**Schedule**: Every day at 8:00 AM
**Timezone**: America/New_York
**Missed Strategy**: Run immediately

### Action
Generate a briefing summarizing:
- Pending approval requests
- New action items
- Active plans
- Yesterday's completed items

### Last Run
2026-02-03T08:00:15 - Success
```

---

## Extended Existing Models

### ActionItemType (Extended)

```python
class ActionItemType(str, Enum):
    """Type of action item (extended for Silver)."""
    FILE_DROP = "file_drop"      # Bronze
    EMAIL = "email"              # Bronze
    WHATSAPP = "whatsapp"        # NEW: Silver
    LINKEDIN = "linkedin"        # NEW: Silver
    SCHEDULED = "scheduled"      # NEW: Silver
```

### SourceType (Extended)

```python
class SourceType(str, Enum):
    """Source of the action item (extended for Silver)."""
    FILESYSTEM = "filesystem"    # Bronze
    GMAIL = "gmail"              # Bronze
    WHATSAPP = "whatsapp"        # NEW: Silver
    LINKEDIN = "linkedin"        # NEW: Silver
    SCHEDULER = "scheduler"      # NEW: Silver
```

---

## Vault Folder Mapping

| Entity | Folder | Status Transitions |
|--------|--------|-------------------|
| ApprovalRequest | `/Pending_Approval/` → `/Approved/` or `/Rejected/` → `/Done/` | PENDING → APPROVED/REJECTED/EXPIRED → EXECUTED |
| Plan | `/Plans/` → `/Done/` | PENDING → IN_PROGRESS → COMPLETED/FAILED |
| PlanStep | (embedded in Plan.md) | PENDING → IN_PROGRESS → COMPLETED/FAILED |
| WhatsAppMessage | `/Needs_Action/WhatsApp/` → `/Done/` | NEW → REVIEWED → RESPONDED → ARCHIVED |
| LinkedInPost | `/Social/LinkedIn/posts/` | DRAFT → SCHEDULED → PENDING_APPROVAL → POSTED |
| LinkedInEngagement | `/Social/LinkedIn/engagement.md` (append) | N/A (log entries) |
| ScheduledTask | `/Schedules/` | (persistent, enabled/disabled) |

---

## Validation Rules

### ApprovalRequest
- `expires_at` must be after `created_at`
- `expires_at` default: 24 hours from `created_at`
- Category must be valid enum value
- Payload must contain required fields for category

### Plan
- Must have at least one step
- Step order must be sequential starting from 1
- Dependency step IDs must exist in plan
- No circular dependencies

### WhatsAppMessage
- Must have at least one matched keyword
- Timestamp must be valid ISO format
- Sender must not be empty

### LinkedInPost
- Content must not exceed LinkedIn character limit (3000 chars)
- `scheduled_at` must be in the future for scheduled posts
- Cannot exceed 25 posts per day per rate limit

### ScheduledTask
- Schedule must be valid cron expression or ISO datetime
- Timezone must be valid IANA timezone identifier
- Action must contain valid action configuration
