"""Odoo ERP data models - Invoice, Payment, and LineItem."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from ai_employee.models.enums import InvoiceStatus, PaymentStatus


@dataclass
class LineItem:
    """A line item on an invoice.

    Attributes:
        description: Description of the service or product
        quantity: Number of units
        unit_price: Price per unit
        tax_rate: Optional tax rate as decimal (e.g., 0.10 for 10%)
        subtotal: Line total before tax
    """

    description: str
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal
    tax_rate: Decimal | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert line item to dictionary."""
        data: dict[str, Any] = {
            "description": self.description,
            "quantity": str(self.quantity),
            "unit_price": str(self.unit_price),
            "subtotal": str(self.subtotal),
        }

        if self.tax_rate is not None:
            data["tax_rate"] = str(self.tax_rate)

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LineItem":
        """Create LineItem from dictionary."""
        return cls(
            description=data["description"],
            quantity=Decimal(str(data["quantity"])),
            unit_price=Decimal(str(data["unit_price"])),
            subtotal=Decimal(str(data["subtotal"])),
            tax_rate=(
                Decimal(str(data["tax_rate"]))
                if data.get("tax_rate") is not None
                else None
            ),
        )


@dataclass
class OdooInvoice:
    """An invoice synced with Odoo ERP.

    Attributes:
        id: Unique identifier (UUID)
        odoo_id: Odoo record ID (set after sync)
        invoice_number: Odoo invoice number (e.g., INV/2026/0001)
        customer_name: Customer display name
        customer_email: Customer email address
        customer_odoo_id: Customer's Odoo partner ID
        line_items: List of invoice line items
        subtotal: Total before tax
        tax_amount: Total tax
        total: Grand total
        amount_paid: Amount already paid
        amount_due: Remaining amount due
        status: Current invoice status
        currency: Currency code (default USD)
        due_date: Payment due date
        created_at: When the invoice was created
        synced_at: When last synced with Odoo
        correlation_id: Correlation ID for tracing
    """

    customer_name: str
    line_items: list[LineItem]
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    status: InvoiceStatus
    id: UUID = field(default_factory=uuid4)
    odoo_id: int | None = None
    invoice_number: str | None = None
    customer_email: str | None = None
    customer_odoo_id: int | None = None
    currency: str = "USD"
    due_date: date | None = None
    created_at: datetime = field(default_factory=datetime.now)
    synced_at: datetime | None = None
    correlation_id: str | None = None

    def is_overdue(self) -> bool:
        """Check if the invoice is past its due date and still has balance.

        Returns:
            True if overdue, False otherwise
        """
        if self.due_date is None:
            return False

        if self.amount_due <= Decimal("0"):
            return False

        return date.today() > self.due_date

    def to_dict(self) -> dict[str, Any]:
        """Convert invoice to dictionary."""
        data: dict[str, Any] = {
            "id": str(self.id),
            "customer_name": self.customer_name,
            "line_items": [item.to_dict() for item in self.line_items],
            "subtotal": str(self.subtotal),
            "tax_amount": str(self.tax_amount),
            "total": str(self.total),
            "amount_paid": str(self.amount_paid),
            "amount_due": str(self.amount_due),
            "status": self.status.value,
            "currency": self.currency,
            "created_at": self.created_at.isoformat(),
        }

        if self.odoo_id is not None:
            data["odoo_id"] = self.odoo_id
        if self.invoice_number is not None:
            data["invoice_number"] = self.invoice_number
        if self.customer_email is not None:
            data["customer_email"] = self.customer_email
        if self.customer_odoo_id is not None:
            data["customer_odoo_id"] = self.customer_odoo_id
        if self.due_date is not None:
            data["due_date"] = self.due_date.isoformat()
        if self.synced_at is not None:
            data["synced_at"] = self.synced_at.isoformat()
        if self.correlation_id is not None:
            data["correlation_id"] = self.correlation_id

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OdooInvoice":
        """Create OdooInvoice from dictionary."""
        line_items = [
            LineItem.from_dict(item) for item in data.get("line_items", [])
        ]

        return cls(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            odoo_id=data.get("odoo_id"),
            invoice_number=data.get("invoice_number"),
            customer_name=data["customer_name"],
            customer_email=data.get("customer_email"),
            customer_odoo_id=data.get("customer_odoo_id"),
            line_items=line_items,
            subtotal=Decimal(str(data["subtotal"])),
            tax_amount=Decimal(str(data["tax_amount"])),
            total=Decimal(str(data["total"])),
            amount_paid=Decimal(str(data["amount_paid"])),
            amount_due=Decimal(str(data["amount_due"])),
            status=InvoiceStatus(data["status"]),
            currency=data.get("currency", "USD"),
            due_date=(
                date.fromisoformat(data["due_date"])
                if data.get("due_date")
                else None
            ),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.now()
            ),
            synced_at=(
                datetime.fromisoformat(data["synced_at"])
                if data.get("synced_at")
                else None
            ),
            correlation_id=data.get("correlation_id"),
        )


@dataclass
class OdooPayment:
    """A payment record synced with Odoo ERP.

    Attributes:
        id: Unique identifier (UUID)
        odoo_id: Odoo record ID (set after sync)
        invoice_id: Local invoice reference
        odoo_invoice_id: Odoo invoice ID
        amount: Payment amount
        currency: Currency code
        payment_date: Date of payment
        payment_method: How the payment was made
        reference: Optional payment reference number
        status: Current payment status
        synced_at: When last synced with Odoo
    """

    invoice_id: str
    amount: Decimal
    currency: str
    payment_date: date
    payment_method: str
    status: PaymentStatus
    id: UUID = field(default_factory=uuid4)
    odoo_id: int | None = None
    odoo_invoice_id: int | None = None
    reference: str | None = None
    synced_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert payment to dictionary."""
        data: dict[str, Any] = {
            "id": str(self.id),
            "invoice_id": self.invoice_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "payment_date": self.payment_date.isoformat(),
            "payment_method": self.payment_method,
            "status": self.status.value,
        }

        if self.odoo_id is not None:
            data["odoo_id"] = self.odoo_id
        if self.odoo_invoice_id is not None:
            data["odoo_invoice_id"] = self.odoo_invoice_id
        if self.reference is not None:
            data["reference"] = self.reference
        if self.synced_at is not None:
            data["synced_at"] = self.synced_at.isoformat()

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OdooPayment":
        """Create OdooPayment from dictionary."""
        return cls(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            odoo_id=data.get("odoo_id"),
            invoice_id=data["invoice_id"],
            odoo_invoice_id=data.get("odoo_invoice_id"),
            amount=Decimal(str(data["amount"])),
            currency=data.get("currency", "USD"),
            payment_date=date.fromisoformat(data["payment_date"]),
            payment_method=data["payment_method"],
            reference=data.get("reference"),
            status=PaymentStatus(data["status"]),
            synced_at=(
                datetime.fromisoformat(data["synced_at"])
                if data.get("synced_at")
                else None
            ),
        )
