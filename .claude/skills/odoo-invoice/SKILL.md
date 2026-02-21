---
name: odoo-invoice
description: Create, manage, and query invoices in Odoo ERP
---

# Odoo Invoice Management

Manage invoices in Odoo ERP via JSON-RPC integration.

## Prerequisites

Set environment variables: ODOO_URL, ODOO_DATABASE, ODOO_USERNAME, ODOO_API_KEY

## Capabilities

- Create customer invoices with line items
- Post (confirm) invoices
- Record payments against invoices
- List invoices with filters (status, customer, date range)
- Get outstanding receivables total
- Generate revenue and expense summaries

## Usage

Use the OdooService from ai_employee.services.odoo:

1. Connect: service.connect_from_env() or service.connect(url, db, user, key)
2. Create customer: service.create_customer(name, email)
3. Create invoice: service.create_invoice(customer_id, line_items, due_date)
4. Post invoice: service.post_invoice(invoice_id)
5. Record payment: service.record_payment(invoice_id, amount, date, method)
6. Reports: service.get_revenue_summary(start, end)
