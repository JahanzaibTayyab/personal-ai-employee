"""Tests for Odoo ERP data models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from ai_employee.models.enums import InvoiceStatus, PaymentStatus
from ai_employee.models.odoo_models import LineItem, OdooInvoice, OdooPayment


class TestLineItem:
    """Tests for LineItem dataclass."""

    def test_create_line_item(self) -> None:
        """Test creating a basic line item."""
        item = LineItem(
            description="Web Development - 10 hours",
            quantity=Decimal("10"),
            unit_price=Decimal("150.00"),
            subtotal=Decimal("1500.00"),
        )

        assert item.description == "Web Development - 10 hours"
        assert item.quantity == Decimal("10")
        assert item.unit_price == Decimal("150.00")
        assert item.subtotal == Decimal("1500.00")
        assert item.tax_rate is None

    def test_create_line_item_with_tax(self) -> None:
        """Test creating a line item with tax rate."""
        item = LineItem(
            description="Consulting",
            quantity=Decimal("5"),
            unit_price=Decimal("200.00"),
            tax_rate=Decimal("0.10"),
            subtotal=Decimal("1000.00"),
        )

        assert item.tax_rate == Decimal("0.10")

    def test_line_item_to_dict(self) -> None:
        """Test converting line item to dictionary."""
        item = LineItem(
            description="Design Work",
            quantity=Decimal("3"),
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("0.05"),
            subtotal=Decimal("300.00"),
        )

        data = item.to_dict()

        assert data["description"] == "Design Work"
        assert data["quantity"] == "3"
        assert data["unit_price"] == "100.00"
        assert data["tax_rate"] == "0.05"
        assert data["subtotal"] == "300.00"

    def test_line_item_to_dict_without_tax(self) -> None:
        """Test converting line item to dict when no tax rate."""
        item = LineItem(
            description="Service",
            quantity=Decimal("1"),
            unit_price=Decimal("50.00"),
            subtotal=Decimal("50.00"),
        )

        data = item.to_dict()
        assert "tax_rate" not in data

    def test_line_item_from_dict(self) -> None:
        """Test creating line item from dictionary."""
        data = {
            "description": "Development",
            "quantity": "8",
            "unit_price": "125.00",
            "tax_rate": "0.07",
            "subtotal": "1000.00",
        }

        item = LineItem.from_dict(data)

        assert item.description == "Development"
        assert item.quantity == Decimal("8")
        assert item.unit_price == Decimal("125.00")
        assert item.tax_rate == Decimal("0.07")
        assert item.subtotal == Decimal("1000.00")

    def test_line_item_from_dict_without_tax(self) -> None:
        """Test creating line item from dict without tax_rate."""
        data = {
            "description": "Support",
            "quantity": "2",
            "unit_price": "75.00",
            "subtotal": "150.00",
        }

        item = LineItem.from_dict(data)
        assert item.tax_rate is None


class TestOdooInvoice:
    """Tests for OdooInvoice dataclass."""

    def test_create_invoice_minimal(self) -> None:
        """Test creating an invoice with minimal fields."""
        invoice = OdooInvoice(
            customer_name="Acme Corp",
            line_items=[],
            subtotal=Decimal("0"),
            tax_amount=Decimal("0"),
            total=Decimal("0"),
            amount_paid=Decimal("0"),
            amount_due=Decimal("0"),
            status=InvoiceStatus.DRAFT,
        )

        assert isinstance(invoice.id, UUID)
        assert invoice.customer_name == "Acme Corp"
        assert invoice.odoo_id is None
        assert invoice.invoice_number is None
        assert invoice.customer_email is None
        assert invoice.customer_odoo_id is None
        assert invoice.currency == "USD"
        assert invoice.due_date is None
        assert invoice.synced_at is None
        assert invoice.correlation_id is None
        assert isinstance(invoice.created_at, datetime)

    def test_create_invoice_full(self) -> None:
        """Test creating an invoice with all fields."""
        line_items = [
            LineItem(
                description="Service A",
                quantity=Decimal("2"),
                unit_price=Decimal("100.00"),
                subtotal=Decimal("200.00"),
            ),
        ]

        invoice = OdooInvoice(
            odoo_id=42,
            invoice_number="INV-2026-001",
            customer_name="Widget Inc",
            customer_email="billing@widget.com",
            customer_odoo_id=7,
            line_items=line_items,
            subtotal=Decimal("200.00"),
            tax_amount=Decimal("20.00"),
            total=Decimal("220.00"),
            amount_paid=Decimal("0"),
            amount_due=Decimal("220.00"),
            status=InvoiceStatus.POSTED,
            currency="EUR",
            due_date=date(2026, 3, 15),
            correlation_id="corr-abc-123",
        )

        assert invoice.odoo_id == 42
        assert invoice.invoice_number == "INV-2026-001"
        assert invoice.customer_email == "billing@widget.com"
        assert invoice.customer_odoo_id == 7
        assert len(invoice.line_items) == 1
        assert invoice.currency == "EUR"
        assert invoice.due_date == date(2026, 3, 15)
        assert invoice.correlation_id == "corr-abc-123"

    def test_invoice_is_overdue_when_past_due(self) -> None:
        """Test that is_overdue returns True when past due date."""
        invoice = OdooInvoice(
            customer_name="Late Payer",
            line_items=[],
            subtotal=Decimal("100"),
            tax_amount=Decimal("0"),
            total=Decimal("100"),
            amount_paid=Decimal("0"),
            amount_due=Decimal("100"),
            status=InvoiceStatus.POSTED,
            due_date=date(2020, 1, 1),
        )

        assert invoice.is_overdue() is True

    def test_invoice_is_not_overdue_when_future_due(self) -> None:
        """Test that is_overdue returns False for future due dates."""
        invoice = OdooInvoice(
            customer_name="Good Client",
            line_items=[],
            subtotal=Decimal("100"),
            tax_amount=Decimal("0"),
            total=Decimal("100"),
            amount_paid=Decimal("0"),
            amount_due=Decimal("100"),
            status=InvoiceStatus.POSTED,
            due_date=date(2099, 12, 31),
        )

        assert invoice.is_overdue() is False

    def test_invoice_is_not_overdue_when_no_due_date(self) -> None:
        """Test that is_overdue returns False when no due date set."""
        invoice = OdooInvoice(
            customer_name="No Due",
            line_items=[],
            subtotal=Decimal("100"),
            tax_amount=Decimal("0"),
            total=Decimal("100"),
            amount_paid=Decimal("0"),
            amount_due=Decimal("100"),
            status=InvoiceStatus.DRAFT,
        )

        assert invoice.is_overdue() is False

    def test_invoice_is_not_overdue_when_paid(self) -> None:
        """Test that is_overdue returns False when fully paid."""
        invoice = OdooInvoice(
            customer_name="Paid Client",
            line_items=[],
            subtotal=Decimal("100"),
            tax_amount=Decimal("0"),
            total=Decimal("100"),
            amount_paid=Decimal("100"),
            amount_due=Decimal("0"),
            status=InvoiceStatus.PAID,
            due_date=date(2020, 1, 1),
        )

        assert invoice.is_overdue() is False

    def test_invoice_to_dict(self) -> None:
        """Test converting invoice to dictionary."""
        line_item = LineItem(
            description="Work",
            quantity=Decimal("1"),
            unit_price=Decimal("500.00"),
            subtotal=Decimal("500.00"),
        )

        invoice = OdooInvoice(
            customer_name="Test Corp",
            line_items=[line_item],
            subtotal=Decimal("500.00"),
            tax_amount=Decimal("50.00"),
            total=Decimal("550.00"),
            amount_paid=Decimal("0"),
            amount_due=Decimal("550.00"),
            status=InvoiceStatus.DRAFT,
        )

        data = invoice.to_dict()

        assert data["customer_name"] == "Test Corp"
        assert data["subtotal"] == "500.00"
        assert data["tax_amount"] == "50.00"
        assert data["total"] == "550.00"
        assert data["status"] == "draft"
        assert data["currency"] == "USD"
        assert len(data["line_items"]) == 1
        assert "id" in data
        assert "created_at" in data

    def test_invoice_from_dict(self) -> None:
        """Test creating invoice from dictionary."""
        data = {
            "id": "12345678-1234-1234-1234-123456789abc",
            "customer_name": "From Dict Corp",
            "line_items": [
                {
                    "description": "Item",
                    "quantity": "2",
                    "unit_price": "50.00",
                    "subtotal": "100.00",
                }
            ],
            "subtotal": "100.00",
            "tax_amount": "10.00",
            "total": "110.00",
            "amount_paid": "0",
            "amount_due": "110.00",
            "status": "draft",
            "currency": "USD",
            "created_at": "2026-02-01T10:00:00",
        }

        invoice = OdooInvoice.from_dict(data)

        assert invoice.customer_name == "From Dict Corp"
        assert invoice.subtotal == Decimal("100.00")
        assert invoice.status == InvoiceStatus.DRAFT
        assert len(invoice.line_items) == 1

    def test_invoice_status_values(self) -> None:
        """Test InvoiceStatus enum has expected values."""
        assert InvoiceStatus.DRAFT.value == "draft"
        assert InvoiceStatus.POSTED.value == "posted"
        assert InvoiceStatus.PARTIAL.value == "partial"
        assert InvoiceStatus.PAID.value == "paid"
        assert InvoiceStatus.OVERDUE.value == "overdue"
        assert InvoiceStatus.CANCELLED.value == "cancelled"


class TestOdooPayment:
    """Tests for OdooPayment dataclass."""

    def test_create_payment_minimal(self) -> None:
        """Test creating a payment with minimal fields."""
        payment = OdooPayment(
            invoice_id="inv-123",
            amount=Decimal("500.00"),
            currency="USD",
            payment_date=date(2026, 2, 15),
            payment_method="bank_transfer",
            status=PaymentStatus.COMPLETED,
        )

        assert isinstance(payment.id, UUID)
        assert payment.invoice_id == "inv-123"
        assert payment.amount == Decimal("500.00")
        assert payment.currency == "USD"
        assert payment.payment_method == "bank_transfer"
        assert payment.status == PaymentStatus.COMPLETED
        assert payment.odoo_id is None
        assert payment.odoo_invoice_id is None
        assert payment.reference is None
        assert payment.synced_at is None

    def test_create_payment_full(self) -> None:
        """Test creating a payment with all fields."""
        synced = datetime(2026, 2, 15, 14, 30, 0)

        payment = OdooPayment(
            odoo_id=99,
            invoice_id="inv-456",
            odoo_invoice_id=42,
            amount=Decimal("1000.00"),
            currency="EUR",
            payment_date=date(2026, 2, 10),
            payment_method="credit_card",
            reference="PAY-2026-099",
            status=PaymentStatus.COMPLETED,
            synced_at=synced,
        )

        assert payment.odoo_id == 99
        assert payment.odoo_invoice_id == 42
        assert payment.reference == "PAY-2026-099"
        assert payment.synced_at == synced

    def test_payment_to_dict(self) -> None:
        """Test converting payment to dictionary."""
        payment = OdooPayment(
            invoice_id="inv-789",
            amount=Decimal("250.50"),
            currency="USD",
            payment_date=date(2026, 3, 1),
            payment_method="wire",
            status=PaymentStatus.PENDING,
        )

        data = payment.to_dict()

        assert data["invoice_id"] == "inv-789"
        assert data["amount"] == "250.50"
        assert data["currency"] == "USD"
        assert data["payment_method"] == "wire"
        assert data["status"] == "pending"
        assert "id" in data

    def test_payment_from_dict(self) -> None:
        """Test creating payment from dictionary."""
        data = {
            "id": "abcdefab-1234-5678-9abc-def012345678",
            "invoice_id": "inv-from-dict",
            "amount": "750.00",
            "currency": "USD",
            "payment_date": "2026-02-20",
            "payment_method": "check",
            "status": "completed",
        }

        payment = OdooPayment.from_dict(data)

        assert payment.invoice_id == "inv-from-dict"
        assert payment.amount == Decimal("750.00")
        assert payment.payment_date == date(2026, 2, 20)
        assert payment.status == PaymentStatus.COMPLETED

    def test_payment_status_values(self) -> None:
        """Test PaymentStatus enum has expected values."""
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.COMPLETED.value == "completed"
        assert PaymentStatus.FAILED.value == "failed"
        assert PaymentStatus.REFUNDED.value == "refunded"
