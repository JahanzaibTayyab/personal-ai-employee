---
name: approve-action
description: List and manage pending approval requests for sensitive actions like emails, social posts, and payments. Use when user asks to see pending approvals, wants to approve or reject actions, check what's waiting for approval, or manage the approval queue.
---

# Approve Action

List and manage pending approval requests in the human-in-the-loop workflow.

## Usage

```
/approve-action [list|approve|reject] [--id <approval_id>]
```

## Quick Start

```bash
# List all pending approvals
scripts/manage_approvals.py list

# Approve a request
scripts/manage_approvals.py approve --id email_20260204_100000

# Reject a request
scripts/manage_approvals.py reject --id email_20260204_100000
```

## Examples

```bash
# List with JSON output
scripts/manage_approvals.py list --json

# Approve specific request
scripts/manage_approvals.py approve --id abc123

# Reject specific request
scripts/manage_approvals.py reject --id def456
```

## List Output

```
## Pending Approvals (3)

| ID | Category | Expires | Summary |
|----|----------|---------|---------|
| email_20260204... | email | 22h | To: client@... Subject: Meeting... |
| linkedin_20260... | social_post | 23h | LinkedIn post |
```

## JSON Output

```json
{
  "success": true,
  "count": 2,
  "approvals": [
    {
      "id": "email_20260204_100000",
      "category": "email",
      "expires_at": "2026-02-05T10:00:00",
      "time_remaining": "22h"
    }
  ]
}
```

## Approval Categories

- `email` - Email send requests
- `social_post` - LinkedIn/social media posts
- `payment` - Payment/financial actions
- `file_operation` - File move/delete/copy
- `custom` - Other sensitive actions

## Manual Approval via Obsidian

Approvals can also be managed by moving files in the vault:

1. Open `/Pending_Approval/` in Obsidian
2. Review the approval request file
3. Move to `/Approved/` to approve
4. Move to `/Rejected/` to reject

## Expiration

- Approvals expire after 24 hours
- Expired approvals auto-rejected
- Dashboard shows stale warnings
