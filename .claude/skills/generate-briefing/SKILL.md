---
name: generate-briefing
description: Generate weekly CEO briefing with business audit
---

# Generate CEO Briefing

Generate a comprehensive weekly CEO briefing report.

## What It Does

Aggregates data from multiple sources into a single executive report:
- Odoo ERP financial data (revenue, expenses, receivables)
- Completed tasks from /Done folder
- Activity log analysis for bottleneck detection
- LinkedIn social media performance metrics
- Cost optimization suggestions (unused subscriptions)

## Usage

Use the BriefingService from ai_employee.services.briefing:

1. Initialize: service = BriefingService(vault_config, odoo_service)
2. Generate: briefing = service.generate_briefing(start, end, goal)
3. Write: filepath = service.write_briefing(briefing)

## Output

Writes a markdown briefing to /Briefings/CEO_Briefing_YYYY-MM-DD.md containing:
- Executive Summary
- Revenue metrics (weekly, MTD, goal progress)
- Completed Tasks table
- Bottleneck alerts with severity levels
- Cost optimization suggestions
- Social media performance
- Upcoming deadlines
