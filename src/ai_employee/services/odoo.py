"""Odoo ERP integration service via JSON-RPC.

Provides customer, invoice, payment, and report operations
using odoorpc for Odoo Community Edition connectivity.
"""

import logging
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import odoorpc

from ai_employee.models.enums import InvoiceStatus, PaymentStatus
from ai_employee.models.odoo_models import LineItem, OdooInvoice, OdooPayment

logger = logging.getLogger(__name__)


class OdooConnectionError(Exception):
    """Raised when Odoo connection is required but not established."""


class OdooOperationError(Exception):
    """Raised when an Odoo operation fails."""


# Mapping from Odoo account.move state to InvoiceStatus
_ODOO_STATE_MAP: dict[str, InvoiceStatus] = {
    "draft": InvoiceStatus.DRAFT,
    "posted": InvoiceStatus.POSTED,
    "cancel": InvoiceStatus.CANCELLED,
}


def _map_odoo_state(
    state: str, amount_residual: float, amount_total: float
) -> InvoiceStatus:
    """Map Odoo account.move state to InvoiceStatus.

    Args:
        state: Odoo state value
        amount_residual: Remaining amount
        amount_total: Total amount

    Returns:
        Corresponding InvoiceStatus
    """
    if state == "posted":
        if amount_residual <= 0:
            return InvoiceStatus.PAID
        if amount_residual < amount_total:
            return InvoiceStatus.PARTIAL
        return InvoiceStatus.POSTED

    return _ODOO_STATE_MAP.get(state, InvoiceStatus.DRAFT)


class OdooService:
    """Service for interacting with Odoo ERP via JSON-RPC.

    Handles CRUD operations for customers, invoices, and payments,
    as well as report generation and operation queuing.
    """

    def __init__(self) -> None:
        """Initialize OdooService in disconnected state."""
        self._client: Any = None
        self._connected: bool = False
        self._database: str = ""
        self._operation_queue: list[dict[str, Any]] = []

    def connect(
        self,
        url: str,
        database: str,
        username: str,
        api_key: str,
    ) -> bool:
        """Connect to Odoo server via JSON-RPC.

        Args:
            url: Odoo server URL (e.g., http://localhost:8069)
            database: Database name
            username: Login username
            api_key: API key or password

        Returns:
            True if connection successful, False otherwise
        """
        try:
            parsed = urlparse(url)
            host = parsed.hostname or "localhost"
            port = parsed.port or (443 if parsed.scheme == "https" else 8069)
            protocol = (
                "jsonrpc+ssl" if parsed.scheme == "https" else "jsonrpc"
            )

            self._client = odoorpc.ODOO(host, port=port, protocol=protocol)
            self._client.login(database, username, api_key)
            self._connected = True
            self._database = database

            logger.info(
                "Connected to Odoo at %s (database: %s)", url, database
            )
            return True

        except Exception as e:
            logger.error("Failed to connect to Odoo: %s", e)
            self._connected = False
            return False

    def connect_from_env(self) -> bool:
        """Connect using environment variables.

        Environment variables:
            ODOO_URL: Server URL
            ODOO_DATABASE: Database name
            ODOO_USERNAME: Login username
            ODOO_API_KEY: API key

        Returns:
            True if connection successful
        """
        return self.connect(
            url=os.environ.get("ODOO_URL", "http://localhost:8069"),
            database=os.environ.get("ODOO_DATABASE", ""),
            username=os.environ.get("ODOO_USERNAME", ""),
            api_key=os.environ.get("ODOO_API_KEY", ""),
        )

    def is_connected(self) -> bool:
        """Check if connected to Odoo.

        Returns:
            True if connected
        """
        return self._connected

    def _require_connection(self) -> None:
        """Raise error if not connected.

        Raises:
            OdooConnectionError: If not connected
        """
        if not self._connected or self._client is None:
            raise OdooConnectionError(
                "Not connected to Odoo. Call connect() first."
            )

    @classmethod
    def from_env(cls) -> "OdooService":
        """Create an OdooService configured from environment variables.

        Returns:
            OdooService instance (not yet connected)
        """
        return cls()

    # ── Customer Operations ──────────────────────────────────────────

    def create_customer(
        self,
        name: str,
        email: str | None = None,
        phone: str | None = None,
        is_company: bool = False,
    ) -> int:
        """Create a customer (res.partner) in Odoo.

        Args:
            name: Customer name
            email: Email address
            phone: Phone number
            is_company: Whether this is a company (vs individual)

        Returns:
            Odoo partner ID

        Raises:
            OdooConnectionError: If not connected
            OdooOperationError: If creation fails
        """
        self._require_connection()

        try:
            partner_data: dict[str, Any] = {
                "name": name,
                "is_company": is_company,
                "customer_rank": 1,
            }

            if email:
                partner_data["email"] = email
            if phone:
                partner_data["phone"] = phone

            partner_model = self._client.env["res.partner"]
            partner_id: int = partner_model.create(partner_data)

            logger.info(
                "Created customer '%s' with ID %d", name, partner_id
            )
            return partner_id

        except OdooConnectionError:
            raise
        except Exception as e:
            raise OdooOperationError(
                f"Failed to create customer '{name}': {e}"
            ) from e

    def get_customer(self, odoo_id: int) -> dict[str, Any] | None:
        """Get a customer by Odoo ID.

        Args:
            odoo_id: Odoo partner ID

        Returns:
            Customer data dict or None if not found

        Raises:
            OdooConnectionError: If not connected
        """
        self._require_connection()

        try:
            partner_model = self._client.env["res.partner"]
            record = partner_model.browse(odoo_id)

            return {
                "id": record.id,
                "name": record.name,
                "email": record.email,
                "phone": record.phone,
                "is_company": record.is_company,
            }

        except Exception as e:
            logger.error("Failed to get customer %d: %s", odoo_id, e)
            return None

    def find_customer_by_email(self, email: str) -> dict[str, Any] | None:
        """Find a customer by email address.

        Args:
            email: Email address to search for

        Returns:
            Customer data dict or None if not found

        Raises:
            OdooConnectionError: If not connected
        """
        self._require_connection()

        try:
            partner_model = self._client.env["res.partner"]
            ids = partner_model.search([("email", "=", email)])

            if not ids:
                return None

            record = partner_model.browse(ids[0])

            return {
                "id": record.id,
                "name": record.name,
                "email": record.email,
                "phone": record.phone,
                "is_company": record.is_company,
            }

        except Exception as e:
            logger.error(
                "Failed to find customer by email '%s': %s", email, e
            )
            return None

    # ── Invoice Operations ───────────────────────────────────────────

    def create_invoice(
        self,
        customer_id: int,
        line_items: list[LineItem],
        due_date: date | None = None,
        reference: str | None = None,
        correlation_id: str | None = None,
    ) -> OdooInvoice:
        """Create an invoice (account.move) in Odoo.

        Args:
            customer_id: Odoo partner ID
            line_items: Invoice line items
            due_date: Payment due date
            reference: External reference
            correlation_id: Correlation ID for tracing

        Returns:
            Created OdooInvoice

        Raises:
            OdooConnectionError: If not connected
            OdooOperationError: If creation fails
        """
        self._require_connection()

        try:
            move_data: dict[str, Any] = {
                "move_type": "out_invoice",
                "partner_id": customer_id,
                "invoice_line_ids": [
                    (0, 0, {
                        "name": item.description,
                        "quantity": float(item.quantity),
                        "price_unit": float(item.unit_price),
                    })
                    for item in line_items
                ],
            }

            if due_date:
                move_data["invoice_date_due"] = due_date.isoformat()
            if reference:
                move_data["ref"] = reference

            move_model = self._client.env["account.move"]
            move_id: int = move_model.create(move_data)
            record = move_model.browse(move_id)

            invoice = self._record_to_invoice(record)
            return OdooInvoice(
                id=invoice.id,
                odoo_id=move_id,
                invoice_number=invoice.invoice_number,
                customer_name=invoice.customer_name,
                customer_email=invoice.customer_email,
                customer_odoo_id=customer_id,
                line_items=line_items,
                subtotal=invoice.subtotal,
                tax_amount=invoice.tax_amount,
                total=invoice.total,
                amount_paid=invoice.amount_paid,
                amount_due=invoice.amount_due,
                status=invoice.status,
                currency=invoice.currency,
                due_date=invoice.due_date,
                created_at=invoice.created_at,
                synced_at=datetime.now(),
                correlation_id=correlation_id,
            )

        except OdooConnectionError:
            raise
        except Exception as e:
            raise OdooOperationError(
                f"Failed to create invoice: {e}"
            ) from e

    def post_invoice(self, invoice_id: int) -> bool:
        """Post (confirm) an invoice in Odoo.

        Args:
            invoice_id: Odoo invoice ID

        Returns:
            True if posted successfully

        Raises:
            OdooConnectionError: If not connected
        """
        self._require_connection()

        try:
            move_model = self._client.env["account.move"]
            record = move_model.browse(invoice_id)
            record.action_post()

            logger.info("Posted invoice %d", invoice_id)
            return True

        except Exception as e:
            logger.error("Failed to post invoice %d: %s", invoice_id, e)
            return False

    def get_invoice(self, odoo_id: int) -> OdooInvoice | None:
        """Get an invoice by Odoo ID.

        Args:
            odoo_id: Odoo account.move ID

        Returns:
            OdooInvoice or None if not found

        Raises:
            OdooConnectionError: If not connected
        """
        self._require_connection()

        try:
            move_model = self._client.env["account.move"]
            record = move_model.browse(odoo_id)
            return self._record_to_invoice(record)

        except Exception as e:
            logger.error("Failed to get invoice %d: %s", odoo_id, e)
            return None

    def list_invoices(
        self,
        status: InvoiceStatus | None = None,
        customer_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 100,
    ) -> list[OdooInvoice]:
        """List invoices with optional filters.

        Args:
            status: Filter by status
            customer_id: Filter by customer Odoo ID
            date_from: Filter from date
            date_to: Filter to date
            limit: Maximum number of results

        Returns:
            List of OdooInvoice objects

        Raises:
            OdooConnectionError: If not connected
        """
        self._require_connection()

        try:
            domain: list[tuple[str, str, Any]] = [
                ("move_type", "=", "out_invoice"),
            ]

            if status:
                odoo_state = self._status_to_odoo_state(status)
                if odoo_state:
                    domain.append(("state", "=", odoo_state))

            if customer_id:
                domain.append(("partner_id", "=", customer_id))

            if date_from:
                domain.append(
                    ("create_date", ">=", date_from.isoformat())
                )

            if date_to:
                domain.append(
                    ("create_date", "<=", date_to.isoformat())
                )

            move_model = self._client.env["account.move"]
            ids = move_model.search(domain, limit=limit)

            invoices: list[OdooInvoice] = []
            for odoo_id in ids:
                record = move_model.browse(odoo_id)
                invoice = self._record_to_invoice(record)
                invoices.append(invoice)

            return invoices

        except OdooConnectionError:
            raise
        except Exception as e:
            logger.error("Failed to list invoices: %s", e)
            return []

    def get_outstanding_receivables(self) -> Decimal:
        """Get total outstanding receivables.

        Returns:
            Total amount of unpaid customer invoices

        Raises:
            OdooConnectionError: If not connected
        """
        self._require_connection()

        try:
            domain: list[tuple[str, str, Any]] = [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("amount_residual", ">", 0),
            ]

            move_model = self._client.env["account.move"]
            ids = move_model.search(domain)

            total = Decimal("0")
            for record in move_model.browse(ids):
                total += Decimal(str(record.amount_residual))

            return total

        except OdooConnectionError:
            raise
        except Exception as e:
            logger.error("Failed to get outstanding receivables: %s", e)
            return Decimal("0")

    # ── Payment Operations ───────────────────────────────────────────

    def record_payment(
        self,
        invoice_id: int,
        amount: Decimal,
        payment_date: date,
        payment_method: str,
        reference: str | None = None,
    ) -> OdooPayment:
        """Record a payment for an invoice.

        Args:
            invoice_id: Odoo invoice ID
            amount: Payment amount
            payment_date: Date of payment
            payment_method: Payment method identifier
            reference: Optional payment reference

        Returns:
            Created OdooPayment

        Raises:
            OdooConnectionError: If not connected
            OdooOperationError: If recording fails
        """
        self._require_connection()

        try:
            # Look up the invoice to get partner_id
            move_model = self._client.env["account.move"]
            invoice_record = move_model.browse(invoice_id)
            partner_id = invoice_record.partner_id.id

            payment_data: dict[str, Any] = {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": partner_id,
                "amount": float(amount),
                "date": payment_date.isoformat(),
                "journal_id": 1,  # Default bank journal
            }

            if reference:
                payment_data["ref"] = reference

            payment_model = self._client.env["account.payment"]
            payment_id: int = payment_model.create(payment_data)
            payment_record = payment_model.browse(payment_id)

            status = (
                PaymentStatus.COMPLETED
                if payment_record.state == "posted"
                else PaymentStatus.PENDING
            )

            return OdooPayment(
                odoo_id=payment_id,
                invoice_id=str(invoice_id),
                odoo_invoice_id=invoice_id,
                amount=amount,
                currency=(
                    payment_record.currency_id.name
                    if hasattr(payment_record, "currency_id")
                    else "USD"
                ),
                payment_date=payment_date,
                payment_method=payment_method,
                reference=reference,
                status=status,
                synced_at=datetime.now(),
            )

        except OdooConnectionError:
            raise
        except Exception as e:
            raise OdooOperationError(
                f"Failed to record payment: {e}"
            ) from e

    # ── Report Operations ────────────────────────────────────────────

    def get_revenue_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Get revenue summary for a date range.

        Args:
            start_date: Period start date
            end_date: Period end date

        Returns:
            Dict with total_invoiced, total_collected,
            total_outstanding, invoice_count

        Raises:
            OdooConnectionError: If not connected
        """
        self._require_connection()

        try:
            domain: list[tuple[str, str, Any]] = [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("create_date", ">=", start_date.isoformat()),
                ("create_date", "<=", end_date.isoformat()),
            ]

            move_model = self._client.env["account.move"]
            ids = move_model.search(domain)
            records = move_model.browse(ids)

            total_invoiced = Decimal("0")
            total_outstanding = Decimal("0")

            record_list = (
                list(records) if hasattr(records, "__iter__") else [records]
            )

            for record in record_list:
                total_invoiced += Decimal(str(record.amount_total))
                total_outstanding += Decimal(str(record.amount_residual))

            total_collected = total_invoiced - total_outstanding

            return {
                "total_invoiced": total_invoiced,
                "total_collected": total_collected,
                "total_outstanding": total_outstanding,
                "invoice_count": len(ids),
            }

        except OdooConnectionError:
            raise
        except Exception as e:
            logger.error("Failed to get revenue summary: %s", e)
            return {
                "total_invoiced": Decimal("0"),
                "total_collected": Decimal("0"),
                "total_outstanding": Decimal("0"),
                "invoice_count": 0,
            }

    def get_expense_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Get expense summary for a date range.

        Args:
            start_date: Period start date
            end_date: Period end date

        Returns:
            Dict with total_expenses and bill_count

        Raises:
            OdooConnectionError: If not connected
        """
        self._require_connection()

        try:
            domain: list[tuple[str, str, Any]] = [
                ("move_type", "=", "in_invoice"),
                ("state", "=", "posted"),
                ("create_date", ">=", start_date.isoformat()),
                ("create_date", "<=", end_date.isoformat()),
            ]

            move_model = self._client.env["account.move"]
            ids = move_model.search(domain)
            records = move_model.browse(ids)

            total_expenses = Decimal("0")

            record_list = (
                list(records) if hasattr(records, "__iter__") else [records]
            )

            for record in record_list:
                total_expenses += Decimal(str(record.amount_total))

            return {
                "total_expenses": total_expenses,
                "bill_count": len(ids),
            }

        except OdooConnectionError:
            raise
        except Exception as e:
            logger.error("Failed to get expense summary: %s", e)
            return {
                "total_expenses": Decimal("0"),
                "bill_count": 0,
            }

    # ── Queue Operations ─────────────────────────────────────────────

    def queue_operation(
        self,
        operation_type: str,
        parameters: dict[str, Any],
    ) -> str:
        """Queue an operation for later processing.

        Operations are queued locally and processed when process_queue()
        is called. This allows offline-first behavior.

        Args:
            operation_type: Type of operation (e.g., "create_invoice")
            parameters: Operation parameters

        Returns:
            Operation ID
        """
        op_id = str(uuid4())

        self._operation_queue.append({
            "id": op_id,
            "type": operation_type,
            "parameters": parameters,
            "queued_at": datetime.now().isoformat(),
            "status": "pending",
        })

        logger.info("Queued operation %s: %s", op_id, operation_type)
        return op_id

    def process_queue(self) -> dict[str, int]:
        """Process all queued operations.

        Returns:
            Dict with processed, failed, and remaining counts
        """
        processed = 0
        failed = 0
        remaining_ops: list[dict[str, Any]] = []

        for operation in self._operation_queue:
            if operation["status"] != "pending":
                continue

            try:
                self._execute_operation(operation)
                processed += 1
            except Exception as e:
                logger.error(
                    "Queue operation %s failed: %s",
                    operation["id"],
                    e,
                )
                remaining_ops.append(
                    {**operation, "status": "failed", "error": str(e)}
                )
                failed += 1

        self._operation_queue = remaining_ops

        return {
            "processed": processed,
            "failed": failed,
            "remaining": len(remaining_ops),
        }

    def _execute_operation(self, operation: dict[str, Any]) -> None:
        """Execute a queued operation.

        Args:
            operation: Operation dict from queue

        Raises:
            OdooOperationError: If execution fails
        """
        op_type = operation["type"]
        params = operation["parameters"]

        if op_type == "create_invoice":
            line_items = [
                LineItem.from_dict(item)
                for item in params.get("line_items", [])
            ]
            self.create_invoice(
                customer_id=params["customer_id"],
                line_items=line_items,
                due_date=(
                    date.fromisoformat(params["due_date"])
                    if params.get("due_date")
                    else None
                ),
            )
        elif op_type == "record_payment":
            self.record_payment(
                invoice_id=params["invoice_id"],
                amount=Decimal(str(params["amount"])),
                payment_date=date.fromisoformat(params["payment_date"]),
                payment_method=params["payment_method"],
            )
        else:
            raise OdooOperationError(
                f"Unknown operation type: {op_type}"
            )

    # ── Private Helpers ──────────────────────────────────────────────

    def _record_to_invoice(self, record: Any) -> OdooInvoice:
        """Convert an Odoo account.move record to OdooInvoice.

        Args:
            record: Odoo record proxy

        Returns:
            OdooInvoice instance
        """
        state = str(record.state)
        amount_total = float(record.amount_total)
        amount_residual = float(record.amount_residual)

        status = _map_odoo_state(state, amount_residual, amount_total)

        # Parse customer info
        customer_name = ""
        customer_email = None
        customer_odoo_id = None
        if hasattr(record, "partner_id") and record.partner_id:
            customer_name = str(record.partner_id.name)
            customer_email = (
                str(record.partner_id.email)
                if record.partner_id.email
                else None
            )
            customer_odoo_id = int(record.partner_id.id)

        # Parse due date
        due_date = None
        if record.invoice_date_due and record.invoice_date_due is not False:
            due_date_str = str(record.invoice_date_due)
            due_date = date.fromisoformat(due_date_str)

        # Parse create date
        created_at = datetime.now()
        if hasattr(record, "create_date") and record.create_date:
            try:
                created_at = datetime.fromisoformat(
                    str(record.create_date)
                )
            except (ValueError, TypeError):
                pass

        # Parse line items
        line_items: list[LineItem] = []
        if hasattr(record, "invoice_line_ids"):
            for line in record.invoice_line_ids:
                try:
                    line_items.append(LineItem(
                        description=str(line.name),
                        quantity=Decimal(str(line.quantity)),
                        unit_price=Decimal(str(line.price_unit)),
                        subtotal=Decimal(str(line.price_subtotal)),
                    ))
                except (AttributeError, ValueError):
                    continue

        # Parse currency
        currency = "USD"
        if hasattr(record, "currency_id") and record.currency_id:
            currency = str(record.currency_id.name)

        return OdooInvoice(
            odoo_id=int(record.id),
            invoice_number=str(record.name) if record.name else None,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_odoo_id=customer_odoo_id,
            line_items=line_items,
            subtotal=Decimal(str(record.amount_untaxed)),
            tax_amount=Decimal(str(record.amount_tax)),
            total=Decimal(str(amount_total)),
            amount_paid=Decimal(str(amount_total - amount_residual)),
            amount_due=Decimal(str(amount_residual)),
            status=status,
            currency=currency,
            due_date=due_date,
            created_at=created_at,
            synced_at=datetime.now(),
        )

    @staticmethod
    def _status_to_odoo_state(status: InvoiceStatus) -> str | None:
        """Map InvoiceStatus to Odoo state value.

        Args:
            status: InvoiceStatus enum

        Returns:
            Odoo state string or None
        """
        mapping: dict[InvoiceStatus, str] = {
            InvoiceStatus.DRAFT: "draft",
            InvoiceStatus.POSTED: "posted",
            InvoiceStatus.PAID: "posted",
            InvoiceStatus.PARTIAL: "posted",
            InvoiceStatus.CANCELLED: "cancel",
        }
        return mapping.get(status)
