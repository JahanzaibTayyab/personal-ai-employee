#!/bin/bash
# ─── AI Employee Demo Vault Setup ────────────────────────────────
# Creates a rich demo vault with realistic data across all tiers.
# Usage: ./scripts/demo_setup.sh [VAULT_PATH]

set -e

VAULT="${1:-/tmp/demo_vault}"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Setting up demo vault at: $VAULT${NC}"

# Clean and init
rm -rf "$VAULT"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"
uv run ai-employee init --vault "$VAULT" > /dev/null 2>&1

# Create Gold tier directories
mkdir -p "$VAULT/Active_Tasks"
mkdir -p "$VAULT/Social/Meta/posts"
mkdir -p "$VAULT/Social/Twitter/tweets"
mkdir -p "$VAULT/Social/LinkedIn/posts"
mkdir -p "$VAULT/Accounting/invoices"
mkdir -p "$VAULT/Archive"

# ─── INBOX (3 items) ─────────────────────────────────────────────
cat > "$VAULT/Inbox/client_proposal_draft.md" << 'EOF'
---
type: file_drop
original_name: client_proposal_draft.md
size: 4096
received: 2026-02-21T07:15:00
priority: normal
status: pending
---
# Proposal: Cloud Migration for Acme Corp

## Executive Summary
Migrate Acme Corp infrastructure to AWS with zero downtime.

## Budget
- Phase 1: $25,000
- Phase 2: $18,000
- Total: $43,000

## Timeline
- Start: March 1, 2026
- Completion: April 15, 2026
EOF

cat > "$VAULT/Inbox/sales_report_q1.csv" << 'EOF'
date,client,amount,product,status
2026-01-05,Acme Corp,15000,Cloud Setup,paid
2026-01-12,Beta LLC,8500,Consulting,paid
2026-01-20,Gamma Inc,12000,Development,pending
2026-02-01,Delta Co,6500,Maintenance,paid
2026-02-15,Epsilon Ltd,22000,Enterprise License,invoiced
EOF

cat > "$VAULT/Inbox/partnership_inquiry.md" << 'EOF'
---
type: email
from: sarah@techpartners.io
subject: Partnership Opportunity - AI Solutions
received: 2026-02-21T09:30:00
priority: high
status: pending
---
Hi,

We'd love to explore a partnership around your AI automation platform.
Our clients in fintech are looking for exactly this type of solution.

Could we schedule a call this week?

Best,
Sarah Chen
VP Business Development, TechPartners
EOF

# ─── NEEDS_ACTION (3 items) ──────────────────────────────────────
cat > "$VAULT/Needs_Action/Email/EMAIL_urgent_client_reply.md" << 'EOF'
---
type: email
from: ceo@acmecorp.com
subject: URGENT - Server downtime affecting production
received: 2026-02-21T06:45:00
priority: urgent
status: pending
---
Our production servers went down at 3 AM. We need immediate support.
Current status: partial outage affecting checkout flow.

## Suggested Actions
- [ ] Reply with ETA for fix
- [ ] Escalate to engineering team
- [ ] Update status page
EOF

cat > "$VAULT/Needs_Action/Email/EMAIL_invoice_request.md" << 'EOF'
---
type: email
from: billing@betalllc.com
subject: Invoice Request for February Services
received: 2026-02-21T08:00:00
priority: normal
status: pending
---
Hi,

Could you send us the invoice for February consulting services?
PO Number: PO-2026-0847

Thanks,
Accounting Team, Beta LLC
EOF

cat > "$VAULT/Needs_Action/WhatsApp/WA_client_pricing.md" << 'EOF'
---
type: whatsapp
from: +1-555-0142 (James, Gamma Inc)
received: 2026-02-21T10:15:00
priority: high
status: pending
keywords_matched: pricing, interested
---
Hey! We're really interested in your enterprise plan. Can you send pricing details? We need it for the board meeting on Friday. Thanks!
EOF

# ─── DONE (5 items) ──────────────────────────────────────────────
for i in 1 2 3 4 5; do
  cat > "$VAULT/Done/completed_task_$i.md" << EOF
---
type: task
completed: 2026-02-$((15+i))T$((8+i)):00:00
priority: normal
status: done
---
Completed task $i - processed successfully.
EOF
done

# ─── QUARANTINE (1 item) ─────────────────────────────────────────
cat > "$VAULT/Quarantine/corrupted_data.md" << 'EOF'
---
type: file_drop
original_name: data_export.json
error: JSON parse error at line 847
quarantined: 2026-02-20T14:30:00
status: quarantined
---
File could not be parsed. Manual review required.
Error: Unexpected token at position 12,847.
EOF

# ─── PENDING_APPROVAL (2 items) ──────────────────────────────────
# Files must be APPROVAL_*.md with YAML frontmatter (matches ApprovalService)
cat > "$VAULT/Pending_Approval/APPROVAL_email_q1_report.md" << 'EOF'
---
id: q1_report_email
category: email
status: pending
created_at: "2026-02-21T09:00:00"
expires_at: "2026-02-22T09:00:00"
payload:
  to: board@company.com
  cc: cfo@company.com
  subject: "Q1 2026 Revenue Report"
  body: "Dear Board Members,\n\nQ1 2026 revenue: $64,000 (+18% QoQ).\n\n- New Clients: 3\n- Recurring Revenue: $42,000\n- Acme Corp deal closed ($15,000)\n- SaaS subscriptions grew to 24 clients\n\nBest regards,\nAI Employee"
---
# Approval Request: Email

**ID**: q1_report_email
**Status**: pending
**Created**: 2026-02-21T09:00:00
**Expires**: 2026-02-22T09:00:00

## Payload

- **to**: board@company.com
- **cc**: cfo@company.com
- **subject**: Q1 2026 Revenue Report
- **body**: Q1 revenue summary for the board
EOF

cat > "$VAULT/Pending_Approval/APPROVAL_social_post_linkedin.md" << 'EOF'
---
id: linkedin_q1_post
category: social_post
status: pending
created_at: "2026-02-21T10:00:00"
expires_at: "2026-02-22T10:00:00"
payload:
  platform: linkedin
  content: "Excited to share that our team just wrapped up an incredible Q1! 18% revenue growth, 3 new enterprise clients onboarded, and our AI automation platform is live. The future of business automation is here. #AI #Automation #BusinessGrowth"
---
# Approval Request: Social Post

**ID**: linkedin_q1_post
**Status**: pending
**Created**: 2026-02-21T10:00:00
**Expires**: 2026-02-22T10:00:00

## Payload

- **platform**: linkedin
- **content**: Q1 results LinkedIn post
EOF

# ─── PLANS (1 active plan) ───────────────────────────────────────
# Files must be PLAN_*.md with YAML frontmatter (matches PlannerService)
cat > "$VAULT/Plans/PLAN_q1_business_review.md" << 'EOF'
---
id: q1_business_review
status: in_progress
created_at: "2026-02-20T09:00:00"
objective: Complete Q1 business review and prepare strategy for Q2
---

# Plan: Complete Q1 business review and prepare strategy for Q2

## Objective

Complete Q1 business review and prepare strategy for Q2

## Steps

1. [x] Gather all Q1 revenue data from invoices and bank transactions
2. [x] Analyze client retention rates and identify churn risks
3. [~] Generate CEO briefing with revenue, bottlenecks, and suggestions
4. [ ] Draft Q2 growth strategy document and share with board

## Status

**Current**: in_progress
**Created**: 2026-02-20 09:00

---
*Auto-generated by AI Employee Planner*
EOF

# ─── SCHEDULES ───────────────────────────────────────────────────
# Files must be *.md with YAML frontmatter (matches SchedulerService)
cat > "$VAULT/Schedules/schedule_daily_briefing.md" << 'EOF'
---
id: schedule_daily_briefing
name: Daily CEO Briefing
schedule: "0 8 * * *"
action:
  type: briefing
enabled: true
timezone: local
missed_strategy: run_immediately
created_at: "2026-02-01T08:00:00"
last_run: "2026-02-21T08:00:00"
next_run: "2026-02-22T08:00:00"
---

# Scheduled Task: Daily CEO Briefing

**Schedule**: `0 8 * * *`
**Type**: briefing
**Enabled**: Yes
**Timezone**: local

**Last Run**: 2026-02-21 08:00
**Next Run**: 2026-02-22 08:00

## Action Configuration

- **type**: briefing
EOF

cat > "$VAULT/Schedules/schedule_weekly_audit.md" << 'EOF'
---
id: schedule_weekly_audit
name: Weekly Business Audit
schedule: "0 21 * * 0"
action:
  type: audit
enabled: true
timezone: local
missed_strategy: run_immediately
created_at: "2026-02-01T21:00:00"
last_run: "2026-02-16T21:00:00"
next_run: "2026-02-23T21:00:00"
---

# Scheduled Task: Weekly Business Audit

**Schedule**: `0 21 * * 0`
**Type**: audit
**Enabled**: Yes
**Timezone**: local

**Last Run**: 2026-02-16 21:00
**Next Run**: 2026-02-23 21:00

## Action Configuration

- **type**: audit
EOF

# ─── BRIEFINGS (2 CEO briefings) ─────────────────────────────────
cat > "$VAULT/Briefings/2026-02-21_Monday_Briefing.md" << 'EOF'
---
generated: 2026-02-21T07:00:00Z
period: 2026-02-14 to 2026-02-20
---
# CEO Weekly Briefing

## Executive Summary
Strong week with revenue ahead of target. Three new client deals closed. One bottleneck in delivery pipeline.

## Revenue
- **This Week**: $12,500
- **Month-to-Date**: $47,500 (95% of $50,000 target)
- **Trend**: On track — projected to exceed monthly target by 8%

## Completed Tasks
- [x] Acme Corp cloud migration Phase 1 delivered
- [x] Beta LLC February invoice sent and paid ($8,500)
- [x] Weekly LinkedIn posts published (3 posts, 2,400 impressions)
- [x] Gamma Inc pricing proposal sent
- [x] Q1 tax documents prepared

## Bottlenecks
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| Delta Co maintenance renewal | 2 days | 5 days | +3 days |

## Proactive Suggestions
### Cost Optimization
- **Unused Software**: Notion Team plan — no activity in 38 days. Cost: $20/month. Consider downgrading.
- **Duplicate Tool**: Both Slack and Teams active. Consolidate to save $15/month.

### Upcoming Deadlines
- Acme Corp Phase 2 kickoff: Feb 25 (4 days)
- Quarterly board meeting: Mar 1 (8 days)
- Epsilon Ltd license renewal: Mar 15 (22 days)

### Growth Opportunities
- Gamma Inc expressed interest in enterprise plan ($22,000 potential)
- TechPartners partnership inquiry received — schedule call

---
*Generated by AI Employee v1.0*
EOF

cat > "$VAULT/Briefings/CEO_Briefing_2026-02-14.md" << 'EOF'
---
generated: 2026-02-14T07:00:00Z
period: 2026-02-07 to 2026-02-13
---
# CEO Weekly Briefing

## Executive Summary
Steady progress. Revenue tracking at 70% of monthly target. No critical blockers.

## Revenue
- **This Week**: $8,500
- **Month-to-Date**: $35,000 (70% of $50,000 target)

## Completed Tasks
- [x] Beta LLC consulting session delivered
- [x] Monthly social media calendar published
- [x] Server infrastructure upgrade completed

---
*Generated by AI Employee v1.0*
EOF

# ─── ACTIVE TASKS (2 Ralph Wiggum tasks) ─────────────────────────
# JSON format with task_id field (matches gold_routes reader)
cat > "$VAULT/Active_Tasks/task_linkedin_audit.json" << 'EOF'
{
  "task_id": "task_linkedin_audit",
  "prompt": "Audit LinkedIn engagement and identify top-performing posts from Q1. Analyze which content types drive the most leads.",
  "status": "paused",
  "iteration": 3,
  "max_iterations": 8,
  "created_at": "2026-02-21T09:00:00",
  "output_summary": "Analyzed 24 posts. Top performers: case studies (3.2% engagement), industry insights (2.8%). Product announcements underperform at 0.9%."
}
EOF

cat > "$VAULT/Active_Tasks/task_inbox_summary.json" << 'EOF'
{
  "task_id": "task_inbox_summary",
  "prompt": "Process all inbox items and generate weekly summary report for the board meeting on Friday.",
  "status": "running",
  "iteration": 4,
  "max_iterations": 10,
  "created_at": "2026-02-21T10:00:00",
  "output_summary": "Processed 3/5 inbox items. 2 emails triaged, 1 proposal reviewed. Generating summary..."
}
EOF

# ─── SOCIAL MEDIA ─────────────────────────────────────────────────
# Meta posts: *.md with YAML frontmatter (matches MetaService.list_posts)
cat > "$VAULT/Social/Meta/posts/META_post_fb_q1_results.md" << 'EOF'
---
id: post_fb_q1_results
platform: facebook
page_id: ""
status: posted
created_at: "2026-02-20T14:00:00"
posted_time: "2026-02-20T15:00:00"
engagement:
  likes: 47
  comments: 8
  shares: 12
  reach: 1850
  impressions: 4200
  last_updated: "2026-02-21T10:00:00"
---
Q1 2026 has been incredible for our team!

18% revenue growth
3 new enterprise clients
AI automation platform launched

Thank you to our amazing clients and partners. Here's to an even bigger Q2!

#BusinessGrowth #AI #Innovation
EOF

cat > "$VAULT/Social/Meta/posts/META_post_ig_team_photo.md" << 'EOF'
---
id: post_ig_team_photo
platform: instagram
page_id: ""
status: draft
created_at: "2026-02-21T11:00:00"
---
Behind the scenes at our AI lab

Building the future of business automation, one line of code at a time.

#TechStartup #AIEmployee #BuildInPublic #StartupLife
EOF

# Tweets: *.md with YAML frontmatter (matches gold_routes get_tweets)
cat > "$VAULT/Social/Twitter/tweets/TWEET_product_launch.md" << 'EOF'
---
id: tweet_product_launch
status: posted
is_thread: false
created_at: "2026-02-19T10:00:00"
posted_time: "2026-02-19T10:30:00"
twitter_id: "1892547301284567890"
engagement:
  likes: 89
  retweets: 23
  replies: 15
  impressions: 5200
  last_updated: "2026-02-21T10:00:00"
---
Just shipped v1.0 of our AI Employee platform

It monitors Gmail, WhatsApp, and social media 24/7, generates CEO briefings, and manages invoices autonomously.

The future of work is here.

#AI #Automation #LaunchDay
EOF

cat > "$VAULT/Social/Twitter/tweets/TWEET_ceo_briefing.md" << 'EOF'
---
id: tweet_ceo_briefing
status: draft
is_thread: false
created_at: "2026-02-21T11:30:00"
---
Every Monday at 8 AM, our AI Employee generates a CEO briefing with:

Revenue summary
Bottleneck analysis
Cost optimization suggestions
Upcoming deadlines

It's like having a COO that never sleeps.
EOF

# ─── INVOICES ─────────────────────────────────────────────────────
# Invoices: *.md with YAML frontmatter (matches gold_routes get_invoices)
# Fields: id, customer_name, amount_total, status, invoice_date, due_date
cat > "$VAULT/Accounting/invoices/INV-2026-001.md" << 'EOF'
---
id: INV-2026-001
customer_name: Acme Corp
amount_total: 15000.00
currency: USD
status: paid
invoice_date: "2026-01-15"
due_date: "2026-02-15"
---
# Invoice INV-2026-001

**Customer**: Acme Corp
**Amount**: $15,000.00
**Status**: Paid (2026-01-22)

## Line Items

| Description | Qty | Unit Price | Total |
|-------------|-----|-----------|-------|
| Cloud Migration Phase 1 | 1 | $15,000.00 | $15,000.00 |

**Total**: $15,000.00
EOF

cat > "$VAULT/Accounting/invoices/INV-2026-002.md" << 'EOF'
---
id: INV-2026-002
customer_name: Beta LLC
amount_total: 8500.00
currency: USD
status: sent
invoice_date: "2026-02-15"
due_date: "2026-03-15"
---
# Invoice INV-2026-002

**Customer**: Beta LLC
**Amount**: $8,500.00
**Status**: Sent (Due: 2026-03-15)

## Line Items

| Description | Qty | Unit Price | Total |
|-------------|-----|-----------|-------|
| February Consulting (40 hrs) | 40 | $200.00 | $8,000.00 |
| Infrastructure Review | 1 | $500.00 | $500.00 |

**Total**: $8,500.00
EOF

# ─── AUDIT LOG ────────────────────────────────────────────────────
# JSONL format with action_type field (matches JS dashboard.js line 881)
cat > "$VAULT/Logs/audit_2026-02-21.log" << 'EOF'
{"timestamp":"2026-02-21T07:00:00Z","action_type":"briefing_generated","actor":"scheduler","target":"2026-02-21_Monday_Briefing.md","result":"success"}
{"timestamp":"2026-02-21T08:00:00Z","action_type":"email_processed","actor":"claude","target":"EMAIL_urgent_client_reply.md","result":"success"}
{"timestamp":"2026-02-21T08:30:00Z","action_type":"email_sent","actor":"email_mcp","target":"board@company.com","result":"success","approval_status":"approved"}
{"timestamp":"2026-02-21T09:00:00Z","action_type":"task_created","actor":"ralph_wiggum","target":"task_linkedin_audit","result":"success"}
{"timestamp":"2026-02-21T09:15:00Z","action_type":"tweet_created","actor":"twitter_service","target":"tweet_ceo_briefing","result":"success"}
{"timestamp":"2026-02-21T10:00:00Z","action_type":"task_created","actor":"ralph_wiggum","target":"task_inbox_summary","result":"success"}
{"timestamp":"2026-02-21T10:30:00Z","action_type":"meta_post_published","actor":"meta_service","target":"post_fb_q1_results","result":"success"}
{"timestamp":"2026-02-21T11:00:00Z","action_type":"invoice_created","actor":"odoo_service","target":"INV-2026-002","result":"success"}
EOF

# ─── DASHBOARD.md ─────────────────────────────────────────────────
cat > "$VAULT/Dashboard.md" << 'EOF'
# AI Employee Dashboard

**Last Updated**: 2026-02-21 11:30 UTC

## Status

| Metric | Count |
|--------|-------|
| Inbox | 3 |
| Needs Action | 3 |
| Completed | 5 |
| Quarantine | 1 |
| Pending Approval | 2 |
| Active Plans | 1 |
| Active Tasks | 2 |

## Watchers
- File Watcher: Running
- Gmail Watcher: Running
- Approval Watcher: Running
- WhatsApp Watcher: Running

## Recent Activity

| Time | Action | Item | Result |
|------|--------|------|--------|
| 11:00 | Invoice created | INV-2026-002 | Success |
| 10:30 | Meta post published | Q1 Results | Success |
| 10:00 | Task started | Inbox Summary | Running |
| 09:15 | Tweet drafted | CEO Briefing tip | Success |
| 09:00 | Task started | LinkedIn Audit | Running |
| 08:30 | Email sent | Q1 Revenue Report | Approved |
| 08:00 | Email processed | Urgent client reply | Success |
| 07:00 | Briefing generated | Monday Briefing | Success |

---
*Auto-generated by AI Employee*
EOF

echo ""
echo -e "${GREEN}Demo vault ready at: $VAULT${NC}"
echo ""
echo "Contents:"
echo "  Inbox:              3 items"
echo "  Needs Action:       3 items (2 email, 1 WhatsApp)"
echo "  Done:               5 items"
echo "  Quarantine:         1 item"
echo "  Pending Approval:   2 items (email + LinkedIn post)"
echo "  Plans:              1 active plan (4 steps)"
echo "  Briefings:          2 CEO briefings"
echo "  Schedules:          2 tasks (daily + weekly)"
echo "  Active Tasks:       2 Ralph Wiggum tasks"
echo "  Social Media:       2 Meta posts, 2 tweets"
echo "  Invoices:           2 invoices"
echo "  Audit Log:          8 entries"
echo ""
echo "Start the dashboard:"
echo "  VAULT_PATH=$VAULT uv run ai-employee web --port 8000"
