# Gold Tier AI Employee - Quickstart Guide

**Created**: 2026-02-21 | **Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

## Prerequisites

Before starting Gold Tier setup:

1. **Silver Tier Complete**: All Silver tier features working
2. **Odoo Community 19+**: Self-hosted instance accessible
3. **Meta Developer Account**: Facebook/Instagram API access
4. **Twitter Developer Account**: API v2 access
5. **Python 3.13+**: With UV package manager

---

## 1. Install Gold Tier Dependencies

```bash
cd ~/personal-ai-employee

# Add new dependencies
uv add odoorpc facebook-sdk tweepy jinja2

# Verify installation
uv run python -c "import odoorpc; import facebook; import tweepy; import jinja2; print('All dependencies installed!')"
```

---

## 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Odoo ERP
ODOO_URL=http://localhost:8069
ODOO_DB=your_company_db
ODOO_USER=admin
ODOO_API_KEY=your_odoo_api_key_or_password

# Meta Graph API (Facebook/Instagram)
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_ACCESS_TOKEN=your_long_lived_page_access_token
META_PAGE_ID=your_facebook_page_id

# Twitter/X API v2
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# Audit settings
AUDIT_RETENTION_DAYS=90
```

---

## 3. Initialize Gold Tier Vault Structure

```bash
# Initialize extended vault structure
uv run ai-employee init --vault ~/AI_Employee_Vault --tier gold
```

This creates:
- `/Active_Tasks/` - Ralph Wiggum task states
- `/Accounting/` - Odoo sync data
- `/Social/Meta/` - Facebook/Instagram posts
- `/Social/Twitter/` - Tweets
- `/Archive/` - Compressed old logs
- `Business_Goals.md` - Template for briefing

---

## 4. Configure Odoo Connection

### 4.1 Get Odoo API Key

In Odoo:
1. Go to Settings > Users & Companies > Users
2. Select your user
3. Go to "API Keys" tab
4. Create new API key

### 4.2 Test Connection

```bash
uv run ai-employee odoo-test --vault ~/AI_Employee_Vault
```

Expected output:
```
Connecting to Odoo at http://localhost:8069...
✓ Connected to database: your_company_db
✓ Authenticated as: admin
✓ Access to invoices: OK
✓ Access to payments: OK
```

---

## 5. Configure Meta (Facebook/Instagram)

### 5.1 Create Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create new app (Business type)
3. Add Facebook Login and Instagram Graph API products
4. Generate long-lived Page Access Token

### 5.2 Test Connection

```bash
uv run ai-employee meta-test --vault ~/AI_Employee_Vault
```

Expected output:
```
Testing Meta Graph API...
✓ Access token valid
✓ Page access: Your Page Name
✓ Instagram linked: @your_instagram_handle
```

---

## 6. Configure Twitter/X

### 6.1 Create Twitter App

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create project and app
3. Generate API keys and access tokens
4. Enable OAuth 1.0a

### 6.2 Test Connection

```bash
uv run ai-employee twitter-test --vault ~/AI_Employee_Vault
```

Expected output:
```
Testing Twitter API v2...
✓ Bearer token valid
✓ User access token valid
✓ Can post tweets: OK
✓ Rate limits: 50/day tweets remaining
```

---

## 7. Set Up Business Goals

Edit `~/AI_Employee_Vault/Business_Goals.md`:

```markdown
---
last_updated: 2026-02-21
review_frequency: weekly
---

## Revenue Targets
monthly_goal: 10000
quarterly_goal: 30000

## Key Metrics
client_response_time_hours: 24
invoice_payment_rate_percent: 90
max_software_costs: 500

## Active Projects
- name: Project Alpha
  due_date: 2026-03-15
  budget: 2000

## Subscription Patterns
tracked_services:
  - netflix.com
  - notion.so
  - slack.com
  - github.com
```

---

## 8. Install Ralph Wiggum Hook

```bash
# Copy hook to Claude Code
cp .claude/hooks/ralph-wiggum-stop.sh ~/.claude/hooks/

# Make executable
chmod +x ~/.claude/hooks/ralph-wiggum-stop.sh

# Configure in Claude Code settings
# Add to ~/.claude/settings.json:
# "hooks": {
#   "stop": ["~/.claude/hooks/ralph-wiggum-stop.sh"]
# }
```

---

## 9. Start Gold Tier Services

```bash
# Start all watchers including new ones
uv run ai-employee watch-all --vault ~/AI_Employee_Vault

# Or start individually:
uv run ai-employee watch-meta --vault ~/AI_Employee_Vault
uv run ai-employee watch-twitter --vault ~/AI_Employee_Vault

# Start watchdog (monitors all watchers)
uv run ai-employee watchdog --vault ~/AI_Employee_Vault
```

---

## 10. Schedule Weekly Briefing

```bash
# Add weekly CEO briefing schedule
uv run ai-employee scheduler --vault ~/AI_Employee_Vault add \
  --name "weekly_ceo_briefing" \
  --schedule "0 21 * * 0" \
  --type briefing

# Verify schedule
uv run ai-employee scheduler --vault ~/AI_Employee_Vault list
```

---

## 11. Test Gold Tier Features

### Test Ralph Wiggum Loop

```bash
# In Claude Code
/ralph-loop "Process all items in /Needs_Action and update Dashboard" --max-iterations 5
```

### Test Odoo Invoice

```bash
# In Claude Code
/odoo-invoice "Create invoice for Client A, 10 hours consulting at $150/hour"
```

### Generate CEO Briefing On-Demand

```bash
# In Claude Code
/generate-briefing
```

### Post to Social Media

```bash
# In Claude Code
/post-facebook "Excited to announce our new service!"
/post-instagram "Check out our latest work!"
/post-twitter "Big news coming soon..."
```

---

## 12. Verify System Health

Check Dashboard.md for service health:

```markdown
## Service Health

| Service | Status | Last Check | Notes |
|---------|--------|------------|-------|
| Gmail | ✅ Healthy | 2m ago | |
| Odoo | ✅ Healthy | 1m ago | |
| Meta | ✅ Healthy | 3m ago | |
| Twitter | ⚠️ Degraded | 5m ago | Rate limited |
| WhatsApp | ✅ Healthy | 2m ago | |
```

---

## Troubleshooting

### Odoo Connection Failed

```bash
# Check Odoo is running
curl http://localhost:8069/web/database/selector

# Verify credentials
uv run python -c "
import odoorpc
odoo = odoorpc.ODOO('localhost', port=8069)
odoo.login('$ODOO_DB', '$ODOO_USER', '$ODOO_API_KEY')
print('Success!')
"
```

### Meta Token Expired

```bash
# Tokens expire after 60 days
# Regenerate at https://developers.facebook.com/tools/explorer/

# Update .env with new token
export META_ACCESS_TOKEN=new_token
```

### Twitter Rate Limited

```bash
# Check current limits
uv run ai-employee twitter-limits

# Free tier limits are very restrictive
# Consider upgrading to Basic tier ($100/month)
```

### Ralph Loop Stuck

```bash
# Check active task state
cat ~/AI_Employee_Vault/Active_Tasks/*.json | jq .

# Force complete task
uv run ai-employee ralph-complete --task-id <task_id>

# Or force fail
uv run ai-employee ralph-fail --task-id <task_id> --reason "Manual abort"
```

---

## Next Steps

1. **Customize Business Goals**: Update metrics and targets
2. **Configure Alerts**: Set up Dashboard notifications
3. **Create Content Calendar**: Schedule social posts
4. **Review First Briefing**: Check Sunday's CEO Briefing
5. **Monitor Audit Logs**: Review `/Logs/audit_*.jsonl`

---

## Upgrade to Platinum Tier

Ready for 24/7 cloud deployment? See the Platinum tier guide:
- Cloud VM setup
- Synced vault configuration
- Multi-agent coordination
