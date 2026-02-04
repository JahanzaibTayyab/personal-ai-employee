# Silver Tier - Quickstart Guide

**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

## Prerequisites

Before starting Silver Tier implementation:

1. **Bronze Tier Complete**: Ensure `001-bronze-ai-employee` is implemented and working
2. **Python 3.13+**: Required for all new dependencies
3. **Obsidian Vault**: Existing vault structure from Bronze tier
4. **API Credentials**: See [Credential Setup](#credential-setup) section

## Quick Install

```bash
# Navigate to project
cd /Users/zaib/Panaverse/personal-ai-employee

# Install Silver tier dependencies
uv add playwright linkedin-api-client workspace-mcp apscheduler sqlalchemy

# Install Playwright browsers
uv run playwright install chromium

# Create new vault folders
uv run ai-employee init-silver --vault ~/AI_Employee_Vault
```

## New Vault Structure

After initialization, your vault will have these new folders:

```
AI_Employee_Vault/
├── Pending_Approval/      # NEW: Actions awaiting your approval
├── Approved/              # NEW: Move approved actions here
├── Rejected/              # NEW: Move rejected actions here
├── Plans/                 # NEW: Active multi-step plans
├── Social/
│   └── LinkedIn/
│       ├── posts/         # NEW: LinkedIn post drafts
│       └── engagement.md  # NEW: Engagement metrics
├── Briefings/             # NEW: Daily/weekly briefings
└── Schedules/             # NEW: Scheduled task configs
```

## Credential Setup

### 1. LinkedIn API (Required for LinkedIn features)

1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create an app with "Sign In with LinkedIn" and "Share on LinkedIn" permissions
3. Note your Client ID and Client Secret

```bash
# Add to .env file
echo 'LINKEDIN_CLIENT_ID=your_client_id' >> .env
echo 'LINKEDIN_CLIENT_SECRET=your_client_secret' >> .env
```

### 2. Google OAuth2 (Required for Gmail MCP)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials (Desktop application type)
3. Enable Gmail API for your project
4. Download credentials JSON

```bash
# Add to .env file
echo 'GOOGLE_CLIENT_ID=your_client_id' >> .env
echo 'GOOGLE_CLIENT_SECRET=your_client_secret' >> .env
echo 'GOOGLE_REDIRECT_URI=http://localhost:8080/callback' >> .env
```

### 3. WhatsApp (No API credentials)

WhatsApp uses browser automation - you'll scan a QR code on first run.

## Running Silver Tier

### Start All Watchers

```bash
# Start all Silver tier watchers
uv run ai-employee watch-all --vault ~/AI_Employee_Vault

# Or start individually:
uv run ai-employee watch                     # File watcher (Bronze)
uv run ai-employee watch-gmail               # Gmail watcher (Bronze)
uv run ai-employee watch-whatsapp            # WhatsApp watcher (Silver)
uv run ai-employee watch-approval            # Approval folder watcher (Silver)
uv run ai-employee watch-linkedin            # LinkedIn engagement (Silver)
```

### Start Scheduler

```bash
# Start the scheduler service
uv run ai-employee scheduler start --vault ~/AI_Employee_Vault

# This will:
# - Enable daily briefings at 8:00 AM
# - Enable weekly audits on Sunday 9:00 PM
# - Check for expired approvals hourly
# - Update Dashboard every 15 minutes
```

### First-Time WhatsApp Setup

```bash
# Initialize WhatsApp session (scan QR code)
uv run ai-employee whatsapp-init

# This opens a browser window
# Scan the QR code with your phone
# Session is saved for future runs
```

### First-Time LinkedIn OAuth

```bash
# Authorize LinkedIn access
uv run ai-employee linkedin-auth

# This opens a browser window
# Login and authorize the app
# Token is saved for future API calls
```

## Using Skills

Once watchers are running, use Claude Code skills:

```bash
# Draft an email (requires approval)
/send-email --to client@example.com --subject "Follow-up" --body "..."

# Schedule a LinkedIn post
/post-linkedin "Excited about our new launch!" --schedule "2026-02-04T10:00:00"

# Create a multi-step plan
/create-plan "Send weekly newsletter to all subscribers"

# List pending approvals
/approve-action list

# Configure a scheduled task
/schedule-task create --name "Daily Standup" --schedule "0 9 * * 1-5" --action briefing
```

## Approval Workflow

The approval workflow is file-based:

1. **Action Detected**: System creates file in `/Pending_Approval/`
2. **Review**: Open file in Obsidian, review the action details
3. **Approve/Reject**:
   - Approve: Move file to `/Approved/`
   - Reject: Move file to `/Rejected/`
4. **Execution**: Approved actions execute within 60 seconds
5. **Completion**: Executed actions move to `/Done/`

**Example approval file:**
```markdown
---
id: approval_20260203_143022_abc123
category: email
status: pending
expires_at: 2026-02-04T14:30:22
---

## Email Approval Request

**To**: client@example.com
**Subject**: Meeting Follow-up

### Body
Thank you for meeting with us today...

---
*Move this file to /Approved/ to send, or /Rejected/ to cancel*
*Expires in 24 hours*
```

## Verifying Installation

Run the health check:

```bash
uv run ai-employee health

# Expected output:
# ✅ Bronze Tier: OK
# ✅ Vault Structure: OK
# ✅ Approval Workflow: OK
# ✅ WhatsApp Session: OK (or ⚠️ Needs QR scan)
# ✅ LinkedIn Auth: OK (or ⚠️ Needs OAuth)
# ✅ Gmail MCP: OK (or ⚠️ Needs OAuth)
# ✅ Scheduler: Running
# ✅ Dashboard: Updated
```

## Common Issues

### WhatsApp Session Expired

```bash
# Re-initialize session
uv run ai-employee whatsapp-init

# Check Dashboard for session status
```

### LinkedIn Rate Limit

- Max 25 posts per day
- Check `/Social/LinkedIn/posts/` for post count
- Scheduled posts queue automatically

### Approval Expired

- Approvals expire after 24 hours
- Expired items auto-move to `/Rejected/`
- Check Dashboard for stale approval alerts

### Scheduler Not Running

```bash
# Check scheduler status
uv run ai-employee scheduler status

# Restart if needed
uv run ai-employee scheduler restart
```

## Next Steps

1. **Configure Keywords**: Edit WhatsApp keywords in config
2. **Set Timezone**: Configure scheduler timezone
3. **Customize Briefings**: Modify briefing templates
4. **Add More Schedules**: Create custom recurring tasks

## Support

- Check Dashboard.md for system status
- Review Logs/ folder for detailed activity
- Run `/check-watcher` skill for watcher health
