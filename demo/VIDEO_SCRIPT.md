# AI Employee Demo Video — Narration Script

**Target Duration**: 5-10 minutes
**Recording Tool**: OBS Studio or QuickTime Player (screen + audio)
**Supporting Assets**: VHS terminal GIFs in `demo/output/`, Playwright screenshots

---

## Pre-Recording Checklist

- [ ] Run `./scripts/demo_setup.sh /tmp/demo_vault` to create demo data
- [ ] Start dashboard: `VAULT_PATH=/tmp/demo_vault uv run ai-employee web --port 8000`
- [ ] Open http://127.0.0.1:8000 in browser
- [ ] Open terminal with the project directory
- [ ] Start OBS/QuickTime screen recording
- [ ] Have this script visible on a second monitor or printed

---

## 0:00 — 0:30 | Introduction

**Show**: Terminal with project README or title slide

**Say**:
> "This is the Personal AI Employee — a digital full-time employee that runs 24/7 on your machine. It monitors Gmail, WhatsApp, and your file system, processes work autonomously, generates CEO briefings, manages social media, handles invoices, and gets human approval before taking sensitive actions. Let me walk you through how it works."

**Action**: Show the README architecture diagram in terminal or browser

---

## 0:30 — 1:30 | Bronze Tier: Foundation

**Show**: Terminal

**Say**:
> "We start with the Bronze tier — the foundation. The system uses an Obsidian vault as its knowledge base. Let's initialize it."

**Action**: Run in terminal:
```bash
uv run ai-employee init --vault /tmp/demo_vault
tree /tmp/demo_vault -L 2 --dirsfirst
```

**Say**:
> "Every folder has a purpose. Inbox holds raw incoming items, Needs_Action queues work for processing, Done stores completed items. The Company Handbook defines processing rules."

**Action**: Show file watcher concept:
```bash
uv run ai-employee watch --vault /tmp/demo_vault --interval 5
```
(Let it run for a few seconds, then Ctrl+C)

**Say**:
> "The file watcher monitors the vault using watchdog. Drop a file in, and it automatically gets detected and routed for processing. We also have a Gmail watcher for monitoring important emails."

---

## 1:30 — 3:00 | Silver Tier: Functional Assistant

**Show**: Dashboard in browser (Overview tab)

**Say**:
> "The Silver tier adds intelligence. Let me show you the web dashboard."

**Action**: Open http://127.0.0.1:8000 — point out:
- Metric cards (Inbox: 3, Needs Action: 3, Completed: 5, Quarantine: 1)
- Pending Approvals panel (2 items)
- Active Plans panel

**Say**:
> "The human-in-the-loop approval workflow is critical. The AI never sends an email or publishes a post without your explicit approval."

**Action**: Click the first approval item (Q1 Revenue Report email)

**Say**:
> "Here's an email to the board with Q1 revenue numbers. I can approve it, reject it, or let it expire. Nothing leaves without my consent."

**Action**: Close the modal. Click the active plan.

**Say**:
> "Plans break complex tasks into steps. This Q1 Business Review has 4 steps — 2 complete, 1 in progress, 1 pending. The AI tracks progress automatically."

**Action**: Close modal. Click "Send Email" quick action, fill the form briefly, then cancel.

**Say**:
> "Quick Actions let me compose emails, create plans, schedule LinkedIn posts — all routed through the approval workflow."

**Action**: Show scheduler in terminal:
```bash
uv run ai-employee scheduler --vault /tmp/demo_vault list
```

**Say**:
> "Scheduled tasks run on cron. Daily CEO briefings at 8 AM, weekly audits every Sunday. Fully configurable."

---

## 3:00 — 5:00 | Gold Tier: Autonomous Employee

**Show**: Browser — Social Media tab

**Action**: Click the "Social Media" tab

**Say**:
> "The Gold tier makes this a true autonomous employee. Here's our social media management. Facebook posts, Instagram content, and tweets — all managed from one dashboard."

**Action**: Click a Meta post to show engagement metrics. Close. Click a tweet.

**Say**:
> "Each post shows engagement data — likes, shares, comments. The AI drafts content and queues it for approval before publishing."

**Action**: Switch to the Operations tab

**Say**:
> "Operations is where the magic happens."

**Action**: Point out Ralph Wiggum Tasks panel

**Say**:
> "Ralph Wiggum is our autonomous execution loop. It takes a task like 'Audit LinkedIn engagement' and runs it iteratively — up to N iterations — with a Stop hook so I can pause or cancel at any time. Here we see one running task and one paused."

**Action**: Click a Ralph Wiggum task to show detail

**Action**: Click a CEO Briefing

**Say**:
> "The weekly CEO briefing is generated automatically every Monday. It includes revenue summary, completed tasks, bottleneck analysis, cost optimization suggestions, and upcoming deadlines. This is the AI acting as your COO."

**Action**: Scroll through the briefing content. Close.

**Action**: Point to invoices panel

**Say**:
> "Invoice management connects to Odoo ERP. We see Acme Corp's paid invoice for $15,000 and Beta LLC's pending invoice for $8,500."

**Action**: Use cross-domain search — type "Acme" and search

**Say**:
> "Cross-domain search correlates data across the entire vault. Searching for 'Acme' finds their proposal in Inbox, their invoice in Accounting, and their mention in the CEO briefing. This is powerful business intelligence."

**Action**: Point to audit log

**Say**:
> "Every action is logged. Briefing generated, email processed, task created, post published — full accountability and traceability."

---

## 5:00 — 6:30 | 24/7 Operation with PM2

**Show**: Terminal

**Say**:
> "Now let's talk about running this 24/7. We use PM2, a production process manager."

**Action**: Run:
```bash
AI_VAULT=/tmp/demo_vault ./scripts/start.sh --only gold
```

**Say**:
> "One command starts all 5 services — file watcher, Gmail watcher, approval watcher, WhatsApp watcher, and the web dashboard. Each runs as its own managed process with auto-restart."

**Action**: Show PM2 status:
```bash
pm2 status
```

**Say**:
> "All 5 processes online. If any crash, PM2 automatically restarts them with configurable delays."

**Action**: Run health check:
```bash
AI_VAULT=/tmp/demo_vault ./scripts/status.sh
```

**Say**:
> "The status script shows process health, vault contents, dashboard availability, and recent activity. Everything in one view."

**Action**:
```bash
./scripts/stop.sh
```

**Say**:
> "And to survive reboots: `pm2 save && pm2 startup`. Your AI Employee starts automatically when your machine boots."

---

## 6:30 — 7:00 | Tests and Code Quality

**Show**: Terminal

**Say**:
> "This project has comprehensive test coverage."

**Action**: Run:
```bash
uv run pytest --tb=short -q
```

**Say**:
> "821 tests covering all three tiers — unit tests, integration tests, and contract tests. Bronze tier, Silver tier, Gold tier — everything tested."

---

## 7:00 — 7:30 | Closing

**Show**: Terminal or title slide

**Say**:
> "To recap — the Personal AI Employee is a three-tier system:
>
> **Bronze**: File and email monitoring with vault-based knowledge management.
> **Silver**: Human-in-the-loop approvals, scheduling, plans, and a web dashboard.
> **Gold**: Autonomous task execution, CEO briefings, social media management, invoice handling, and cross-domain intelligence.
>
> It runs 24/7 with PM2, every action is auditable, and nothing sensitive happens without human approval. This is the future of personal AI — a digital FTE that works while you sleep."

**Action**: Show the dashboard one final time

**Say**:
> "Thank you for watching."

---

## Post-Recording

1. Trim the video to 5-10 minutes
2. Add title card at the beginning
3. Optionally insert VHS terminal GIFs from `demo/output/` as picture-in-picture
4. Upload to YouTube or the hackathon submission platform
