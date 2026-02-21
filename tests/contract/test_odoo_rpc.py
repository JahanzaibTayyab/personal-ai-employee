"""Contract tests for Odoo JSON-RPC integration.

These tests verify the contract between OdooService and the Odoo server.
All Odoo server calls are mocked to simulate the expected API behavior.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.models.enums import InvoiceStatus, PaymentStatus
from ai_employee.models.odoo_models import LineItem, OdooInvoice
from ai_employee.services.odoo import OdooService


@pytest.fixture
def mock_odoo_server() -> MagicMock:
    """Create a mock Odoo server with expected model behaviors."""
    server = MagicMock()

    # Mock res.partner model
    partner_model = MagicMock()
    partner_record = MagicMock()
    partner_record.id = 1
    partner_record.name = "Contract Test Corp"
    partner_record.email = "contract@test.com"
    partner_record.phone = "+1555000000"
    partner_record.is_company = True
    partner_model.create.return_value = 1
    partner_model.search.return_value = [1]
    partner_model.browse.return_value = partner_record

    # Mock account.move model
    move_model = MagicMock()
    invoice_record = MagicMock()
    invoice_record.id = 10
    invoice_record.name = "INV/2026/0010"
    invoice_record.partner_id = partner_record
    invoice_record.state = "draft"
    invoice_record.amount_untaxed = 1000.0
    invoice_record.amount_tax = 100.0
    invoice_record.amount_total = 1100.0
    invoice_record.amount_residual = 1100.0
    invoice_record.currency_id = MagicMock()
    invoice_record.currency_id.name = "USD"
    invoice_record.invoice_date_due = "2026-04-01"
    invoice_record.create_date = "2026-02-21 10:00:00"
    invoice_record.invoice_line_ids = []
    move_model.create.return_value = 10
    move_model.browse.return_value = invoice_record
    move_model.search.return_value = [10]

    # Mock account.payment model
    payment_model = MagicMock()
    payment_record = MagicMock()
    payment_record.id = 20
    payment_record.name = "PAY/2026/0020"
    payment_record.state = "posted"
    payment_record.amount = 1100.0
    payment_record.currency_id = MagicMock()
    payment_record.currency_id.name = "USD"
    payment_record.date = "2026-02-21"
    payment_model.create.return_value = 20
    payment_model.browse.return_value = payment_record

    def get_model(name: str) -> MagicMock:
        models = {
            "res.partner": partner_model,
            "account.move": move_model,
            "account.payment": payment_model,
        }
        return models.get(name, MagicMock())

    server.env = MagicMock()
    server.env.__getitem__ = MagicMock(side_effect=get_model)

    return server


@pytest.fixture
def service_with_mock_server(mock_odoo_server: MagicMock) -> OdooService:
    """Create an OdooService connected to a mock Odoo server."""
    service = OdooService()
    service._client = mock_odoo_server
    service._connected = True
    service._database = "contract_test_db"
    return service


class TestOdooRPCCustomerContract:
    """Contract tests for customer (res.partner) operations."""

    def test_create_customer_sends_correct_fields(
        self, service_with_mock_server: OdooService, mock_odoo_server: MagicMock
    ) -> None:
        """Verify create_customer sends the expected fields to res.partner."""
        service_with_mock_server.create_customer(
            name="New Corp",
            email="new@corp.com",
            phone="+1999888777",
            is_company=True,
        )

        partner_model = mock_odoo_server.env["res.partner"]
        call_args = partner_model.create.call_args[0][0]

        assert call_args["name"] == "New Corp"
        assert call_args["email"] == "new@corp.com"
        assert call_args["phone"] == "+1999888777"
        assert call_args["is_company"] is True

    def test_find_customer_by_email_uses_correct_domain(
        self, service_with_mock_server: OdooService, mock_odoo_server: MagicMock
    ) -> None:
        """Verify find_customer_by_email searches with correct domain filter."""
        service_with_mock_server.find_customer_by_email("search@test.com")

        partner_model = mock_odoo_server.env["res.partner"]
        search_domain = partner_model.search.call_args[0][0]

        # Should search by email
        assert any(
            item[0] == "email" and item[2] == "search@test.com"
            for item in search_domain
        )


class TestOdooRPCInvoiceContract:
    """Contract tests for invoice (account.move) operations."""

    def test_create_invoice_sends_correct_structure(
        self, service_with_mock_server: OdooService, mock_odoo_server: MagicMock
    ) -> None:
        """Verify create_invoice creates the expected account.move record."""
        line_items = [
            LineItem(
                description="Contract Service",
                quantity=Decimal("5"),
                unit_price=Decimal("200.00"),
                subtotal=Decimal("1000.00"),
            ),
        ]

        service_with_mock_server.create_invoice(
            customer_id=1,
            line_items=line_items,
            due_date=date(2026, 4, 1),
            reference="CONTRACT-001",
        )

        move_model = mock_odoo_server.env["account.move"]
        call_args = move_model.create.call_args[0][0]

        assert call_args["move_type"] == "out_invoice"
        assert call_args["partner_id"] == 1
        assert call_args["ref"] == "CONTRACT-001"
        assert "invoice_line_ids" in call_args

    def test_post_invoice_calls_action_post(
        self, service_with_mock_server: OdooService, mock_odoo_server: MagicMock
    ) -> None:
        """Verify post_invoice calls action_post on the account.move record."""
        service_with_mock_server.post_invoice(10)

        move_model = mock_odoo_server.env["account.move"]
        move_model.browse.assert_called()
        invoice_record = move_model.browse.return_value
        invoice_record.action_post.assert_called_once()

    def test_list_invoices_uses_correct_domain(
        self, service_with_mock_server: OdooService, mock_odoo_server: MagicMock
    ) -> None:
        """Verify list_invoices builds correct search domain."""
        service_with_mock_server.list_invoices(
            status=InvoiceStatus.POSTED,
            customer_id=1,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 12, 31),
            limit=50,
        )

        move_model = mock_odoo_server.env["account.move"]
        move_model.search.assert_called_once()
        search_args = move_model.search.call_args

        domain = search_args[0][0]

        # Should filter by type
        assert any(
            item[0] == "move_type" and item[2] == "out_invoice"
            for item in domain
        )

    def test_get_outstanding_receivables_filters_correctly(
        self, service_with_mock_server: OdooService, mock_odoo_server: MagicMock
    ) -> None:
        """Verify get_outstanding_receivables uses correct filters."""
        service_with_mock_server.get_outstanding_receivables()

        move_model = mock_odoo_server.env["account.move"]
        move_model.search.assert_called_once()
        search_args = move_model.search.call_args
        domain = search_args[0][0]

        # Should filter for customer invoices with outstanding amounts
        assert any(
            item[0] == "move_type" and item[2] == "out_invoice"
            for item in domain
        )
        assert any(
            item[0] == "amount_residual" and item[1] == ">"
            for item in domain
        )


class TestOdooRPCPaymentContract:
    """Contract tests for payment (account.payment) operations."""

    def test_record_payment_sends_correct_structure(
        self, service_with_mock_server: OdooService, mock_odoo_server: MagicMock
    ) -> None:
        """Verify record_payment creates the expected account.payment record."""
        service_with_mock_server.record_payment(
            invoice_id=10,
            amount=Decimal("1100.00"),
            payment_date=date(2026, 2, 21),
            payment_method="bank_transfer",
            reference="PAY-REF-001",
        )

        payment_model = mock_odoo_server.env["account.payment"]
        call_args = payment_model.create.call_args[0][0]

        assert call_args["payment_type"] == "inbound"
        assert call_args["amount"] == 1100.0
        assert "partner_id" in call_args


class TestOdooRPCReportContract:
    """Contract tests for report generation."""

    def test_revenue_summary_queries_out_invoices(
        self, service_with_mock_server: OdooService, mock_odoo_server: MagicMock
    ) -> None:
        """Verify revenue summary only queries customer invoices."""
        service_with_mock_server.get_revenue_summary(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
        )

        move_model = mock_odoo_server.env["account.move"]
        domain = move_model.search.call_args[0][0]

        assert any(
            item[0] == "move_type" and item[2] == "out_invoice"
            for item in domain
        )

    def test_expense_summary_queries_in_invoices(
        self, service_with_mock_server: OdooService, mock_odoo_server: MagicMock
    ) -> None:
        """Verify expense summary only queries vendor bills."""
        service_with_mock_server.get_expense_summary(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
        )

        move_model = mock_odoo_server.env["account.move"]
        domain = move_model.search.call_args[0][0]

        assert any(
            item[0] == "move_type" and item[2] == "in_invoice"
            for item in domain
        )


class TestOdooRPCConnectionContract:
    """Contract tests for connection behavior."""

    @patch("ai_employee.services.odoo.odoorpc")
    def test_connect_uses_correct_parameters(
        self, mock_rpc_module: MagicMock
    ) -> None:
        """Verify connect passes correct parameters to odoorpc."""
        mock_client = MagicMock()
        mock_rpc_module.ODOO.return_value = mock_client

        service = OdooService()
        service.connect(
            url="http://odoo.example.com:8069",
            database="production",
            username="admin",
            api_key="key-123",
        )

        mock_rpc_module.ODOO.assert_called_once_with(
            "odoo.example.com", port=8069, protocol="jsonrpc"
        )
        mock_client.login.assert_called_once_with(
            "production", "admin", "key-123"
        )

    @patch("ai_employee.services.odoo.odoorpc")
    def test_connect_https_uses_jsonrpc_ssl(
        self, mock_rpc_module: MagicMock
    ) -> None:
        """Verify HTTPS URLs use jsonrpc+ssl protocol."""
        mock_client = MagicMock()
        mock_rpc_module.ODOO.return_value = mock_client

        service = OdooService()
        service.connect(
            url="https://odoo.example.com",
            database="production",
            username="admin",
            api_key="key-123",
        )

        mock_rpc_module.ODOO.assert_called_once_with(
            "odoo.example.com", port=443, protocol="jsonrpc+ssl"
        )
