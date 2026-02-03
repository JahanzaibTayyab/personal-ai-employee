---
name: send-email
description: Draft and send emails with human-in-the-loop approval. Use when user wants to send an email, compose a message, draft correspondence, or send any email communication. All emails require approval before sending.
---

# Send Email

Draft an email for approval and sending via Gmail MCP.

## Usage

```
/send-email --to <recipient> --subject <subject> --body <body> [--cc <cc>] [--attachments <files>]
```

## Quick Start

Run the script to create an email request:

```bash
scripts/create_email_request.py --to "client@example.com" --subject "Meeting Follow-up" --body "Thank you..."
```

## Arguments

- `--to` (required): Recipient email address
- `--subject` (required): Email subject line
- `--body` (required): Email body content
- `--cc` (optional): CC recipients (comma-separated)
- `--bcc` (optional): BCC recipients (comma-separated)
- `--attachments` (optional): File paths (comma-separated)

## Examples

```bash
# Simple email
scripts/create_email_request.py --to "client@example.com" --subject "Hello" --body "Message here"

# With CC and attachments
scripts/create_email_request.py --to "team@company.com" --cc "manager@company.com" \
  --subject "Weekly Report" --body "Please find attached..." \
  --attachments "/path/to/report.pdf"

# JSON output
scripts/create_email_request.py --to "user@example.com" --subject "Test" --body "Test" --json
```

## Workflow

1. Run `scripts/create_email_request.py` with email details
2. Script creates approval request in `/Pending_Approval/`
3. User reviews and moves file to `/Approved/` in Obsidian
4. Approval watcher sends via Google Workspace MCP
5. Result logged and file moved to `/Done/`

## Output

```json
{
  "success": true,
  "request_id": "email_20260204_100000",
  "approval_file": "/Pending_Approval/APPROVAL_email_20260204_100000.md",
  "to": "client@example.com",
  "subject": "Meeting Follow-up",
  "expires_at": "2026-02-05T10:00:00"
}
```

## Approval Actions

- **Approve**: Move file to `/Approved/`
- **Reject**: Move file to `/Rejected/`
- **Edit**: Modify content before approving
- **Expire**: Auto-rejected after 24 hours
