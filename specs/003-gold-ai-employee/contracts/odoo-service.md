# Odoo ERP Service Contract

**Version**: 1.0.0 | **Created**: 2026-02-21

## Overview

Service for integrating with Odoo Community Edition via JSON-RPC external API.

---

## Interface: OdooService

### Connection Methods

#### connect

Establish connection to Odoo.

**Input**:
```python
def connect(
    url: str = None,  # Default from env
    database: str = None,
    username: str = None,
    api_key: str = None
) -> bool
```

**Output**: True if connected successfully

**Errors**:
- `OdooConnectionError`: Cannot reach Odoo server
- `OdooAuthenticationError`: Invalid credentials

---

#### is_connected

Check if connection is active.

**Input**:
```python
def is_connected() -> bool
```

---

### Customer (Partner) Methods

#### create_customer

Create a new customer in Odoo.

**Input**:
```python
def create_customer(
    name: str,
    email: str = None,
    phone: str = None,
    is_company: bool = True
) -> int  # Returns Odoo partner ID
```

**Errors**:
- `OdooConnectionError`: Not connected
- `OdooValidationError`: Invalid customer data

---

#### get_customer

Get customer by Odoo ID.

**Input**:
```python
def get_customer(odoo_id: int) -> Optional[dict]
```

---

#### find_customer_by_email

Find customer by email address.

**Input**:
```python
def find_customer_by_email(email: str) -> Optional[dict]
```

---

### Invoice Methods

#### create_invoice

Create a draft invoice in Odoo.

**Input**:
```python
def create_invoice(
    customer_id: int,
    line_items: list[dict],  # [{description, quantity, unit_price, tax_rate?}]
    due_date: date = None,
    reference: str = None,
    correlation_id: str = None
) -> OdooInvoice
```

**Output**: OdooInvoice model with odoo_id populated

**Errors**:
- `OdooConnectionError`: Not connected
- `CustomerNotFoundError`: Invalid customer_id
- `OdooValidationError`: Invalid line items

---

#### post_invoice

Post a draft invoice (make it official).

**Input**:
```python
def post_invoice(invoice_id: int) -> OdooInvoice
```

**Errors**:
- `InvoiceNotFoundError`: Invalid invoice_id
- `InvalidInvoiceStateError`: Invoice not in draft state

---

#### get_invoice

Get invoice by Odoo ID.

**Input**:
```python
def get_invoice(odoo_id: int) -> Optional[OdooInvoice]
```

---

#### list_invoices

List invoices with filters.

**Input**:
```python
def list_invoices(
    status: InvoiceStatus = None,
    customer_id: int = None,
    date_from: date = None,
    date_to: date = None,
    limit: int = 100
) -> list[OdooInvoice]
```

---

#### get_outstanding_receivables

Get unpaid invoices.

**Input**:
```python
def get_outstanding_receivables() -> list[OdooInvoice]
```

---

### Payment Methods

#### record_payment

Record a payment against an invoice.

**Input**:
```python
def record_payment(
    invoice_id: int,
    amount: Decimal,
    payment_date: date,
    payment_method: str,
    reference: str = None
) -> OdooPayment
```

**Errors**:
- `InvoiceNotFoundError`: Invalid invoice_id
- `InvalidPaymentAmountError`: Amount exceeds balance due
- `InvalidInvoiceStateError`: Invoice not posted

---

### Reporting Methods

#### get_revenue_summary

Get revenue summary for a period.

**Input**:
```python
def get_revenue_summary(
    start_date: date,
    end_date: date
) -> dict
```

**Output**:
```python
{
    "total_invoiced": Decimal,
    "total_paid": Decimal,
    "outstanding": Decimal,
    "invoice_count": int,
    "payment_count": int
}
```

---

#### get_expense_summary

Get expense summary for a period.

**Input**:
```python
def get_expense_summary(
    start_date: date,
    end_date: date
) -> dict
```

**Output**:
```python
{
    "total_expenses": Decimal,
    "by_category": dict[str, Decimal],
    "transaction_count": int
}
```

---

### Queue Methods

#### queue_operation

Queue an operation for later execution when Odoo is unavailable.

**Input**:
```python
def queue_operation(
    operation_type: str,
    parameters: dict
) -> str  # Returns queue ID
```

---

#### process_queue

Process all queued operations.

**Input**:
```python
def process_queue() -> dict
```

**Output**:
```python
{
    "processed": int,
    "failed": int,
    "remaining": int
}
```

---

## Events

| Event | When | Payload |
|-------|------|---------|
| `odoo_connected` | Connection established | url |
| `odoo_disconnected` | Connection lost | url, error |
| `customer_created` | New customer | odoo_id, name |
| `invoice_created` | Invoice drafted | odoo_id, total |
| `invoice_posted` | Invoice posted | odoo_id, invoice_number |
| `payment_recorded` | Payment made | invoice_id, amount |
| `operation_queued` | Odoo unavailable | operation_type |
| `queue_processed` | Queue completed | processed_count |

---

## Error Handling

All Odoo operations should:
1. Check connection status before operation
2. If disconnected, attempt reconnection once
3. If still disconnected, queue the operation
4. Log all operations to audit log
5. Update service health status
