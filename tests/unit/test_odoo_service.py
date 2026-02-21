"""Tests for OdooService - all odoorpc calls mocked."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.models.enums import InvoiceStatus, PaymentStatus
from ai_employee.models.odoo_models import LineItem, OdooInvoice, OdooPayment
from ai_employee.services.odoo import OdooConnectionError, OdooService


@pytest.fixture
def mock_odoorpc() -> MagicMock:
    """Create a mock odoorpc.ODOO instance."""
    mock = MagicMock()
    mock.env = MagicMock()
    return mock


@pytest.fixture
def odoo_service() -> OdooService:
    """Create an OdooService instance (not connected)."""
    return OdooService()


@pytest.fixture
def connected_service(odoo_service: OdooService, mock_odoorpc: MagicMock) -> OdooService:
    """Create a connected OdooService instance."""
    odoo_service._client = mock_odoorpc
    odoo_service._connected = True
    odoo_service._database = "test_db"
    return odoo_service


class TestOdooServiceConnection:
    """Tests for OdooService connection management."""

    @patch("ai_employee.services.odoo.odoorpc")
    def test_connect_success(
        self, mock_rpc_module: MagicMock, odoo_service: OdooService
    ) -> None:
        """Test successful connection to Odoo."""
        mock_client = MagicMock()
        mock_rpc_module.ODOO.return_value = mock_client

        result = odoo_service.connect(
            url="http://localhost:8069",
            database="test_db",
            username="admin",
            api_key="test-key-123",
        )

        assert result is True
        assert odoo_service.is_connected() is True
        mock_client.login.assert_called_once_with("test_db", "admin", "test-key-123")

    @patch("ai_employee.services.odoo.odoorpc")
    def test_connect_failure(
        self, mock_rpc_module: MagicMock, odoo_service: OdooService
    ) -> None:
        """Test connection failure raises error."""
        mock_rpc_module.ODOO.side_effect = Exception("Connection refused")

        result = odoo_service.connect(
            url="http://invalid:8069",
            database="test_db",
            username="admin",
            api_key="bad-key",
        )

        assert result is False
        assert odoo_service.is_connected() is False

    def test_is_connected_when_not_connected(self, odoo_service: OdooService) -> None:
        """Test is_connected returns False initially."""
        assert odoo_service.is_connected() is False

    @patch("ai_employee.services.odoo.odoorpc")
    def test_connect_from_env(self, mock_rpc_module: MagicMock) -> None:
        """Test connecting using environment variables."""
        mock_client = MagicMock()
        mock_rpc_module.ODOO.return_value = mock_client

        env_vars = {
            "ODOO_URL": "http://odoo.local:8069",
            "ODOO_DATABASE": "production",
            "ODOO_USERNAME": "admin",
            "ODOO_API_KEY": "api-key-xyz",
        }

        with patch.dict("os.environ", env_vars):
            service = OdooService.from_env()
            result = service.connect_from_env()

        assert result is True


class TestOdooServiceCustomers:
    """Tests for OdooService customer operations."""

    def test_create_customer(self, connected_service: OdooService) -> None:
        """Test creating a customer in Odoo."""
        mock_partner = MagicMock()
        mock_partner.create.return_value = 42
        connected_service._client.env.__getitem__.return_value = mock_partner

        result = connected_service.create_customer(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890",
            is_company=True,
        )

        assert result == 42
        mock_partner.create.assert_called_once()

    def test_get_customer(self, connected_service: OdooService) -> None:
        """Test getting a customer by Odoo ID."""
        mock_partner = MagicMock()
        mock_record = MagicMock()
        mock_record.name = "Test Customer"
        mock_record.email = "test@example.com"
        mock_record.phone = "+1234567890"
        mock_record.is_company = True
        mock_record.id = 42
        mock_partner.browse.return_value = mock_record
        connected_service._client.env.__getitem__.return_value = mock_partner

        result = connected_service.get_customer(42)

        assert result is not None
        assert result["name"] == "Test Customer"
        assert result["email"] == "test@example.com"
        assert result["id"] == 42

    def test_find_customer_by_email(self, connected_service: OdooService) -> None:
        """Test finding a customer by email address."""
        mock_partner = MagicMock()
        mock_partner.search.return_value = [42]
        mock_record = MagicMock()
        mock_record.name = "Found Customer"
        mock_record.email = "found@example.com"
        mock_record.phone = ""
        mock_record.is_company = False
        mock_record.id = 42
        mock_partner.browse.return_value = mock_record
        connected_service._client.env.__getitem__.return_value = mock_partner

        result = connected_service.find_customer_by_email("found@example.com")

        assert result is not None
        assert result["name"] == "Found Customer"

    def test_find_customer_by_email_not_found(
        self, connected_service: OdooService
    ) -> None:
        """Test finding a non-existent customer returns None."""
        mock_partner = MagicMock()
        mock_partner.search.return_value = []
        connected_service._client.env.__getitem__.return_value = mock_partner

        result = connected_service.find_customer_by_email("nobody@example.com")

        assert result is None

    def test_create_customer_not_connected(self, odoo_service: OdooService) -> None:
        """Test creating customer when not connected raises error."""
        with pytest.raises(OdooConnectionError):
            odoo_service.create_customer(name="Test", email="t@t.com")


class TestOdooServiceInvoices:
    """Tests for OdooService invoice operations."""

    def test_create_invoice(self, connected_service: OdooService) -> None:
        """Test creating an invoice in Odoo."""
        mock_move = MagicMock()
        mock_move.create.return_value = 100
        mock_record = MagicMock()
        mock_record.id = 100
        mock_record.name = "INV/2026/0001"
        mock_record.state = "draft"
        mock_record.amount_untaxed = 1500.0
        mock_record.amount_tax = 150.0
        mock_record.amount_total = 1650.0
        mock_record.amount_residual = 1650.0
        mock_record.currency_id = MagicMock()
        mock_record.currency_id.name = "USD"
        mock_record.invoice_date_due = "2026-03-15"
        mock_record.create_date = "2026-02-15 10:00:00"
        mock_move.browse.return_value = mock_record
        connected_service._client.env.__getitem__.return_value = mock_move

        line_items = [
            LineItem(
                description="Consulting",
                quantity=Decimal("10"),
                unit_price=Decimal("150.00"),
                subtotal=Decimal("1500.00"),
            ),
        ]

        invoice = connected_service.create_invoice(
            customer_id=42,
            line_items=line_items,
            due_date=date(2026, 3, 15),
            reference="PO-2026-001",
            correlation_id="corr-123",
        )

        assert isinstance(invoice, OdooInvoice)
        assert invoice.odoo_id == 100
        assert invoice.customer_name is not None

    def test_post_invoice(self, connected_service: OdooService) -> None:
        """Test posting (confirming) an invoice."""
        mock_move = MagicMock()
        mock_record = MagicMock()
        mock_record.state = "posted"
        mock_move.browse.return_value = mock_record
        connected_service._client.env.__getitem__.return_value = mock_move

        result = connected_service.post_invoice(100)

        assert result is True
        mock_record.action_post.assert_called_once()

    def test_get_invoice(self, connected_service: OdooService) -> None:
        """Test getting an invoice by Odoo ID."""
        mock_move = MagicMock()
        mock_record = MagicMock()
        mock_record.id = 100
        mock_record.name = "INV/2026/0001"
        mock_record.partner_id = MagicMock()
        mock_record.partner_id.name = "Test Customer"
        mock_record.partner_id.email = "test@example.com"
        mock_record.partner_id.id = 42
        mock_record.state = "posted"
        mock_record.amount_untaxed = 500.0
        mock_record.amount_tax = 50.0
        mock_record.amount_total = 550.0
        mock_record.amount_residual = 550.0
        mock_record.currency_id = MagicMock()
        mock_record.currency_id.name = "USD"
        mock_record.invoice_date_due = "2026-03-01"
        mock_record.create_date = "2026-02-01 09:00:00"
        mock_record.invoice_line_ids = []
        mock_move.browse.return_value = mock_record
        connected_service._client.env.__getitem__.return_value = mock_move

        invoice = connected_service.get_invoice(100)

        assert invoice is not None
        assert invoice.odoo_id == 100
        assert invoice.customer_name == "Test Customer"
        assert invoice.status == InvoiceStatus.POSTED

    def test_list_invoices(self, connected_service: OdooService) -> None:
        """Test listing invoices with filters."""
        mock_move = MagicMock()
        mock_move.search.return_value = [100, 101]

        mock_record_1 = MagicMock()
        mock_record_1.id = 100
        mock_record_1.name = "INV/2026/0001"
        mock_record_1.partner_id = MagicMock()
        mock_record_1.partner_id.name = "Customer A"
        mock_record_1.partner_id.email = "a@test.com"
        mock_record_1.partner_id.id = 1
        mock_record_1.state = "posted"
        mock_record_1.amount_untaxed = 100.0
        mock_record_1.amount_tax = 10.0
        mock_record_1.amount_total = 110.0
        mock_record_1.amount_residual = 110.0
        mock_record_1.currency_id = MagicMock()
        mock_record_1.currency_id.name = "USD"
        mock_record_1.invoice_date_due = "2026-03-01"
        mock_record_1.create_date = "2026-02-01 09:00:00"
        mock_record_1.invoice_line_ids = []

        mock_record_2 = MagicMock()
        mock_record_2.id = 101
        mock_record_2.name = "INV/2026/0002"
        mock_record_2.partner_id = MagicMock()
        mock_record_2.partner_id.name = "Customer B"
        mock_record_2.partner_id.email = "b@test.com"
        mock_record_2.partner_id.id = 2
        mock_record_2.state = "draft"
        mock_record_2.amount_untaxed = 200.0
        mock_record_2.amount_tax = 20.0
        mock_record_2.amount_total = 220.0
        mock_record_2.amount_residual = 220.0
        mock_record_2.currency_id = MagicMock()
        mock_record_2.currency_id.name = "USD"
        mock_record_2.invoice_date_due = False
        mock_record_2.create_date = "2026-02-02 09:00:00"
        mock_record_2.invoice_line_ids = []

        mock_move.browse.side_effect = [mock_record_1, mock_record_2]
        connected_service._client.env.__getitem__.return_value = mock_move

        invoices = connected_service.list_invoices(limit=10)

        assert len(invoices) == 2
        assert invoices[0].odoo_id == 100
        assert invoices[1].odoo_id == 101

    def test_get_outstanding_receivables(self, connected_service: OdooService) -> None:
        """Test getting total outstanding receivables."""
        mock_move = MagicMock()
        mock_move.search.return_value = [100, 101]

        mock_record_1 = MagicMock()
        mock_record_1.amount_residual = 500.0
        mock_record_2 = MagicMock()
        mock_record_2.amount_residual = 300.0

        mock_move.browse.return_value = [mock_record_1, mock_record_2]
        connected_service._client.env.__getitem__.return_value = mock_move

        total = connected_service.get_outstanding_receivables()

        assert total == Decimal("800.0")

    def test_create_invoice_not_connected(self, odoo_service: OdooService) -> None:
        """Test creating invoice when not connected raises error."""
        with pytest.raises(OdooConnectionError):
            odoo_service.create_invoice(customer_id=1, line_items=[])


class TestOdooServicePayments:
    """Tests for OdooService payment operations."""

    def test_record_payment(self, connected_service: OdooService) -> None:
        """Test recording a payment for an invoice."""
        mock_payment = MagicMock()
        mock_payment.create.return_value = 200
        mock_payment_record = MagicMock()
        mock_payment_record.id = 200
        mock_payment_record.name = "PAY/2026/0001"
        mock_payment_record.state = "posted"
        mock_payment_record.amount = 550.0
        mock_payment_record.currency_id = MagicMock()
        mock_payment_record.currency_id.name = "USD"
        mock_payment_record.date = "2026-02-15"
        mock_payment.browse.return_value = mock_payment_record

        # Mock account.move for invoice lookup
        mock_move = MagicMock()
        mock_invoice = MagicMock()
        mock_invoice.id = 100
        mock_invoice.partner_id = MagicMock()
        mock_invoice.partner_id.id = 42
        mock_move.browse.return_value = mock_invoice

        def get_model(name: str) -> MagicMock:
            if name == "account.payment":
                return mock_payment
            return mock_move

        connected_service._client.env.__getitem__.side_effect = get_model

        payment = connected_service.record_payment(
            invoice_id=100,
            amount=Decimal("550.00"),
            payment_date=date(2026, 2, 15),
            payment_method="bank_transfer",
            reference="REF-001",
        )

        assert isinstance(payment, OdooPayment)
        assert payment.odoo_id == 200
        assert payment.status == PaymentStatus.COMPLETED

    def test_record_payment_not_connected(self, odoo_service: OdooService) -> None:
        """Test recording payment when not connected raises error."""
        with pytest.raises(OdooConnectionError):
            odoo_service.record_payment(
                invoice_id=1,
                amount=Decimal("100"),
                payment_date=date(2026, 1, 1),
                payment_method="cash",
            )


class TestOdooServiceReports:
    """Tests for OdooService report generation."""

    def test_get_revenue_summary(self, connected_service: OdooService) -> None:
        """Test getting revenue summary for a period."""
        mock_move = MagicMock()
        mock_move.search.return_value = [100, 101, 102]

        record_1 = MagicMock()
        record_1.amount_total = 1000.0
        record_1.amount_residual = 0.0
        record_1.state = "posted"

        record_2 = MagicMock()
        record_2.amount_total = 2000.0
        record_2.amount_residual = 500.0
        record_2.state = "posted"

        record_3 = MagicMock()
        record_3.amount_total = 1500.0
        record_3.amount_residual = 1500.0
        record_3.state = "posted"

        mock_move.browse.return_value = [record_1, record_2, record_3]
        connected_service._client.env.__getitem__.return_value = mock_move

        summary = connected_service.get_revenue_summary(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
        )

        assert "total_invoiced" in summary
        assert "total_collected" in summary
        assert "total_outstanding" in summary
        assert "invoice_count" in summary

    def test_get_expense_summary(self, connected_service: OdooService) -> None:
        """Test getting expense summary for a period."""
        mock_move = MagicMock()
        mock_move.search.return_value = [200]

        record = MagicMock()
        record.amount_total = 500.0
        record.state = "posted"

        mock_move.browse.return_value = [record]
        connected_service._client.env.__getitem__.return_value = mock_move

        summary = connected_service.get_expense_summary(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
        )

        assert "total_expenses" in summary
        assert "bill_count" in summary


class TestOdooServiceQueue:
    """Tests for OdooService operation queue."""

    def test_queue_operation(self, connected_service: OdooService) -> None:
        """Test queuing an operation for later processing."""
        op_id = connected_service.queue_operation(
            operation_type="create_invoice",
            parameters={"customer_id": 42, "amount": "100.00"},
        )

        assert op_id is not None
        assert isinstance(op_id, str)

    def test_process_queue(self, connected_service: OdooService) -> None:
        """Test processing queued operations."""
        # Queue some operations first
        connected_service.queue_operation(
            operation_type="create_invoice",
            parameters={"customer_id": 42},
        )

        result = connected_service.process_queue()

        assert "processed" in result
        assert "failed" in result
        assert "remaining" in result

    def test_queue_operation_not_connected(self, odoo_service: OdooService) -> None:
        """Test queueing operation when not connected still works (queued locally)."""
        op_id = odoo_service.queue_operation(
            operation_type="create_invoice",
            parameters={"customer_id": 42},
        )

        assert op_id is not None
