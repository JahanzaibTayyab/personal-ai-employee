# Gold Tier AI Employee - Data Model

**Created**: 2026-02-21 | **Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

## Overview

This document defines the data models for Gold Tier features: Ralph Wiggum loop state, Odoo integration, CEO briefings, social media posts, audit logging, and service health tracking.

---

## 1. TaskState (Ralph Wiggum Loop)

Represents the state of an active autonomous task being executed by the Ralph Wiggum loop.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| task_id | string (UUID) | Yes | Unique identifier for the task |
| prompt | string | Yes | Original task prompt to re-inject |
| iteration | integer | Yes | Current iteration count (starts at 1) |
| max_iterations | integer | Yes | Maximum allowed iterations (default: 10) |
| status | TaskStatus enum | Yes | pending, in_progress, paused, completed, failed |
| completion_strategy | string | Yes | "promise" or "file_movement" |
| completion_promise | string | No | Token Claude outputs when complete (if promise strategy) |
| context | string | No | Previous output and state for context injection |
| requires_approval | boolean | Yes | Whether task is paused waiting for approval |
| approval_id | string | No | Reference to approval request if paused |
| created_at | datetime | Yes | When task was created |
| updated_at | datetime | Yes | Last update timestamp |
| completed_at | datetime | No | When task completed (if applicable) |

### State Transitions

```
pending → in_progress → (paused → in_progress)* → completed|failed
```

### File Location

`/Active_Tasks/{task_id}.json`

---

## 2. OdooInvoice

Represents an invoice created or synced from Odoo ERP.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (UUID) | Yes | Local identifier |
| odoo_id | integer | No | Odoo's internal ID (null if pending sync) |
| invoice_number | string | No | Odoo invoice reference (e.g., INV/2026/0001) |
| customer_name | string | Yes | Customer/partner name |
| customer_email | string | No | Customer email for notifications |
| customer_odoo_id | integer | No | Odoo partner ID |
| line_items | list[LineItem] | Yes | Invoice line items |
| subtotal | decimal | Yes | Sum of line items before tax |
| tax_amount | decimal | Yes | Total tax amount |
| total | decimal | Yes | Grand total (subtotal + tax) |
| amount_paid | decimal | Yes | Amount already paid |
| amount_due | decimal | Yes | Remaining balance (total - paid) |
| status | InvoiceStatus enum | Yes | draft, posted, paid, cancelled |
| currency | string | Yes | Currency code (default: USD) |
| due_date | date | No | Payment due date |
| created_at | datetime | Yes | When created locally |
| synced_at | datetime | No | Last sync with Odoo |
| correlation_id | string | No | Link to triggering action (e.g., WhatsApp request) |

### LineItem (embedded)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| description | string | Yes | Line item description |
| quantity | decimal | Yes | Quantity |
| unit_price | decimal | Yes | Price per unit |
| tax_rate | decimal | No | Tax rate as percentage |
| subtotal | decimal | Yes | quantity × unit_price |

### File Location

`/Accounting/invoices/{id}.md` (local tracking)

---

## 3. OdooPayment

Represents a payment recorded in Odoo.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (UUID) | Yes | Local identifier |
| odoo_id | integer | No | Odoo's internal ID |
| invoice_id | string | Yes | Reference to local invoice ID |
| odoo_invoice_id | integer | No | Reference to Odoo invoice ID |
| amount | decimal | Yes | Payment amount |
| currency | string | Yes | Currency code |
| payment_date | date | Yes | When payment was made |
| payment_method | string | Yes | bank_transfer, credit_card, cash, etc. |
| reference | string | No | Payment reference/transaction ID |
| status | PaymentStatus enum | Yes | pending, completed, failed |
| synced_at | datetime | No | Last sync with Odoo |

### File Location

`/Accounting/payments/{id}.md`

---

## 4. CEOBriefing

Represents a generated weekly business briefing.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Date-based ID (YYYY-MM-DD) |
| period_start | date | Yes | Start of reporting period |
| period_end | date | Yes | End of reporting period |
| executive_summary | string | Yes | AI-generated summary |
| revenue_this_week | decimal | Yes | Revenue for the period |
| revenue_mtd | decimal | Yes | Month-to-date revenue |
| monthly_goal | decimal | No | Target from Business_Goals.md |
| revenue_trend | string | Yes | "on_track", "ahead", "behind" |
| completed_tasks | list[CompletedTask] | Yes | Tasks completed in period |
| bottlenecks | list[Bottleneck] | No | Tasks that took longer than expected |
| cost_suggestions | list[CostSuggestion] | No | Unused subscription recommendations |
| upcoming_deadlines | list[Deadline] | No | Tasks due soon |
| social_media_summary | SocialSummary | No | Engagement metrics across platforms |
| audit_summary | AuditSummary | No | Action counts and anomalies |
| generated_at | datetime | Yes | When briefing was generated |

### CompletedTask (embedded)

| Field | Type | Required |
|-------|------|----------|
| title | string | Yes |
| completed_at | datetime | Yes |
| source | string | No |

### Bottleneck (embedded)

| Field | Type | Required |
|-------|------|----------|
| task | string | Yes |
| expected_days | integer | Yes |
| actual_days | integer | Yes |
| delay_days | integer | Yes |

### CostSuggestion (embedded)

| Field | Type | Required |
|-------|------|----------|
| service | string | Yes |
| reason | string | Yes |
| monthly_cost | decimal | Yes |
| action | string | Yes |

### File Location

`/Briefings/{id}_Monday_Briefing.md`

---

## 5. MetaPost

Represents a Facebook or Instagram post.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (UUID) | Yes | Local identifier |
| platform | string | Yes | "facebook" or "instagram" |
| platform_id | string | No | Meta's post ID after publishing |
| page_id | string | Yes | Target page/account ID |
| content | string | Yes | Post text content |
| media_urls | list[string] | No | URLs of attached media |
| media_type | string | No | "image", "video", "carousel" |
| scheduled_time | datetime | No | When to publish |
| posted_time | datetime | No | When actually published |
| status | PostStatus enum | Yes | draft, scheduled, pending_approval, approved, posted, failed |
| approval_id | string | No | Reference to approval request |
| engagement | MetaEngagement | No | Engagement metrics (after posting) |
| error_message | string | No | Error if posting failed |
| cross_post | boolean | Yes | Whether to post to both FB and IG |
| created_at | datetime | Yes | When created |
| correlation_id | string | No | Link to triggering action |

### MetaEngagement (embedded)

| Field | Type | Required |
|-------|------|----------|
| likes | integer | Yes |
| comments | integer | Yes |
| shares | integer | Yes |
| reach | integer | No |
| impressions | integer | No |
| last_updated | datetime | Yes |

### File Location

`/Social/Meta/posts/{id}.md`

---

## 6. Tweet

Represents a Twitter/X post.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (UUID) | Yes | Local identifier |
| twitter_id | string | No | Twitter's tweet ID after publishing |
| content | string | Yes | Tweet text (max 280 chars) |
| media_ids | list[string] | No | Twitter media IDs for attachments |
| thread_parent_id | string | No | Parent tweet ID if part of thread |
| thread_position | integer | No | Position in thread (1, 2, 3...) |
| scheduled_time | datetime | No | When to publish |
| posted_time | datetime | No | When actually published |
| status | PostStatus enum | Yes | draft, scheduled, pending_approval, approved, posted, failed |
| approval_id | string | No | Reference to approval request |
| engagement | TweetEngagement | No | Engagement metrics (after posting) |
| is_thread | boolean | Yes | Whether this starts or is part of a thread |
| error_message | string | No | Error if posting failed |
| created_at | datetime | Yes | When created |
| correlation_id | string | No | Link to triggering action |

### TweetEngagement (embedded)

| Field | Type | Required |
|-------|------|----------|
| likes | integer | Yes |
| retweets | integer | Yes |
| replies | integer | Yes |
| quote_tweets | integer | No |
| impressions | integer | No |
| last_updated | datetime | Yes |

### File Location

`/Social/Twitter/tweets/{id}.md`

---

## 7. AuditEntry

Represents a single audit log entry.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | datetime | Yes | When action occurred |
| action_type | string | Yes | Category of action (email_send, invoice_create, etc.) |
| actor | string | Yes | Who/what performed action (claude_code, scheduler, user) |
| target | string | Yes | What was acted upon |
| parameters | dict | No | Action-specific parameters |
| approval_status | string | Yes | not_required, pending, approved, rejected |
| approved_by | string | No | Who approved (if applicable) |
| result | string | Yes | success, failure, partial |
| error_message | string | No | Error details if failed |
| correlation_id | string | No | Links related actions across domains |
| duration_ms | integer | No | How long action took |

### Action Types

- `email_draft`, `email_send`, `email_read`
- `invoice_create`, `invoice_post`, `payment_record`
- `post_facebook`, `post_instagram`, `post_twitter`
- `task_start`, `task_complete`, `task_fail`
- `approval_request`, `approval_granted`, `approval_rejected`
- `watcher_start`, `watcher_stop`, `watcher_restart`
- `briefing_generate`
- `ralph_loop_start`, `ralph_loop_iterate`, `ralph_loop_complete`

### File Location

`/Logs/audit_YYYY-MM-DD.jsonl` (one entry per line)

---

## 8. ServiceHealth

Tracks the health status of external services.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| service_name | string | Yes | Unique service identifier |
| display_name | string | Yes | Human-readable name |
| status | HealthStatus enum | Yes | healthy, degraded, unavailable |
| last_check | datetime | Yes | When last health check ran |
| last_success | datetime | No | Last successful operation |
| consecutive_failures | integer | Yes | Number of failures in a row |
| last_error | string | No | Most recent error message |
| error_category | string | No | transient, auth, logic, data, system |
| is_critical | boolean | Yes | Whether system depends on this service |
| queued_operations | integer | Yes | Number of operations waiting for service |

### Services Tracked

- `gmail` - Gmail API via workspace-mcp
- `odoo` - Odoo ERP JSON-RPC
- `meta` - Meta Graph API (Facebook/Instagram)
- `twitter` - Twitter/X API v2
- `linkedin` - LinkedIn API
- `whatsapp` - WhatsApp Web session
- `filesystem` - Local vault access

### File Location

`/Logs/health_YYYY-MM-DD.log` (heartbeats)
Dashboard.md (current status)

---

## Enum Definitions

### TaskStatus
```python
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
```

### InvoiceStatus
```python
class InvoiceStatus(Enum):
    DRAFT = "draft"
    POSTED = "posted"
    PAID = "paid"
    CANCELLED = "cancelled"
```

### PaymentStatus
```python
class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
```

### PostStatus
```python
class PostStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    POSTED = "posted"
    FAILED = "failed"
```

### HealthStatus
```python
class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
```

---

## Relationships

```
TaskState --[triggers]--> ApprovalRequest (when requires_approval=true)
TaskState --[has]--> correlation_id (links to originating action)

OdooInvoice --[has many]--> OdooPayment
OdooInvoice --[has]--> correlation_id (links to WhatsApp/Email request)

CEOBriefing --[aggregates]--> OdooInvoice (revenue)
CEOBriefing --[aggregates]--> Done/* (completed tasks)
CEOBriefing --[aggregates]--> AuditEntry (action summary)
CEOBriefing --[aggregates]--> MetaPost, Tweet (social engagement)

MetaPost --[has]--> ApprovalRequest (via approval_id)
MetaPost --[has]--> correlation_id (links to campaign/plan)

Tweet --[has]--> ApprovalRequest (via approval_id)
Tweet --[has]--> Tweet (thread relationship via thread_parent_id)

AuditEntry --[has]--> correlation_id (links related actions)

ServiceHealth --[monitors]--> all external services
```

---

## Migration from Silver Tier

No breaking changes to existing models. Gold tier adds new models:

1. Create `/Active_Tasks/` directory
2. Create `/Accounting/` with subdirectories
3. Create `/Social/Meta/` and `/Social/Twitter/` directories
4. Create `/Archive/` for log archival
5. Add `Business_Goals.md` template to vault root
6. Extend Dashboard.md with service health section
