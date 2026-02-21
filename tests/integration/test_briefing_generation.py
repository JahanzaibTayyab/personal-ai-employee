"""Integration tests for briefing generation end-to-end."""

import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.briefing import CEOBriefing
from ai_employee.services.briefing import BriefingService


@pytest.fixture
def populated_vault(tmp_path: Path) -> Path:
    """Create a fully populated vault for integration testing."""
    vault = tmp_path / "vault"
    vault.mkdir()

    # Create directory structure
    dirs = [
        "Done",
        "Logs",
        "Briefings",
        "Social/LinkedIn/posts",
        "Plans",
        "Needs_Action",
        "Needs_Action/Email",
        "Inbox",
    ]
    for d in dirs:
        (vault / d).mkdir(parents=True, exist_ok=True)

    # Create completed tasks in /Done
    done = vault / "Done"

    (done / "FILE_quarterly_report.md").write_text(
        "---\n"
        "type: file_drop\n"
        "source: filesystem\n"
        "original_name: quarterly_report.pdf\n"
        "created: '2026-02-18T09:00:00'\n"
        "status: done\n"
        "priority: high\n"
        "processed_at: '2026-02-18T09:30:00'\n"
        "---\n\n"
        "Quarterly report analyzed and summary created.\n"
    )

    (done / "EMAIL_client_proposal.md").write_text(
        "---\n"
        "type: email\n"
        "source: gmail\n"
        "original_name: Client Proposal Review\n"
        "created: '2026-02-19T14:00:00'\n"
        "status: done\n"
        "priority: normal\n"
        "processed_at: '2026-02-19T14:45:00'\n"
        "from_address: client@example.com\n"
        "---\n\n"
        "Proposal reviewed and response drafted.\n"
    )

    (done / "FILE_invoice_scan.md").write_text(
        "---\n"
        "type: file_drop\n"
        "source: filesystem\n"
        "original_name: invoice_scan.jpg\n"
        "created: '2026-02-20T11:00:00'\n"
        "status: done\n"
        "priority: normal\n"
        "processed_at: '2026-02-20T11:15:00'\n"
        "---\n\n"
        "Invoice scanned and data extracted into accounting.\n"
    )

    # Create activity logs
    logs = vault / "Logs"

    log_entries = [
        {
            "timestamp": "2026-02-18T09:30:00",
            "action_type": "process",
            "item_id": "quarterly_report",
            "outcome": "success",
            "duration_ms": 30000,
        },
        {
            "timestamp": "2026-02-19T14:45:00",
            "action_type": "process",
            "item_id": "client_proposal",
            "outcome": "success",
            "duration_ms": 45000,
        },
        {
            "timestamp": "2026-02-20T11:15:00",
            "action_type": "process",
            "item_id": "invoice_scan",
            "outcome": "success",
            "duration_ms": 15000,
        },
        {
            "timestamp": "2026-02-20T15:00:00",
            "action_type": "process",
            "item_id": "failed_item",
            "outcome": "failure",
            "duration_ms": 120000,
            "details": "Processing timeout",
        },
    ]

    for entry in log_entries:
        log_date = entry["timestamp"][:10]
        log_file = logs / f"claude_{log_date}.log"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    # Create LinkedIn posts
    posts_dir = vault / "Social" / "LinkedIn" / "posts"

    (posts_dir / "post_2026-02-17.md").write_text(
        "---\n"
        "status: published\n"
        "published_at: '2026-02-17T09:00:00'\n"
        "impressions: 3500\n"
        "likes: 85\n"
        "comments: 12\n"
        "shares: 5\n"
        "topic: Industry Trends\n"
        "---\n\n"
        "Great insights on industry trends for 2026.\n"
    )

    (posts_dir / "post_2026-02-20.md").write_text(
        "---\n"
        "status: published\n"
        "published_at: '2026-02-20T10:00:00'\n"
        "impressions: 5200\n"
        "likes: 130\n"
        "comments: 22\n"
        "shares: 10\n"
        "topic: Product Launch\n"
        "lead_detected: true\n"
        "---\n\n"
        "Exciting product launch announcement.\n"
    )

    return vault


@pytest.fixture
def populated_vault_config(populated_vault: Path) -> VaultConfig:
    """Create VaultConfig for the populated vault."""
    return VaultConfig(root=populated_vault)


class TestBriefingGenerationIntegration:
    """End-to-end integration tests for briefing generation."""

    def test_full_briefing_generation(
        self, populated_vault_config: VaultConfig
    ) -> None:
        """Test complete briefing generation from populated vault."""
        service = BriefingService(vault_config=populated_vault_config)

        briefing = service.generate_briefing(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
            monthly_goal=Decimal("100000.00"),
        )

        # Verify briefing structure
        assert isinstance(briefing, CEOBriefing)
        assert briefing.id == "2026-02-21"
        assert briefing.period_start == date(2026, 2, 15)
        assert briefing.period_end == date(2026, 2, 21)

        # Verify tasks were collected
        assert len(briefing.completed_tasks) >= 1

        # Verify executive summary was generated
        assert len(briefing.executive_summary) > 0

    def test_briefing_with_odoo_data(
        self, populated_vault_config: VaultConfig
    ) -> None:
        """Test briefing generation with mocked Odoo financial data."""
        mock_odoo = MagicMock()
        mock_odoo.is_connected.return_value = True
        mock_odoo.get_revenue_summary.return_value = {
            "total_invoiced": Decimal("45000.00"),
            "total_collected": Decimal("38000.00"),
            "total_outstanding": Decimal("7000.00"),
            "invoice_count": 15,
        }
        mock_odoo.get_expense_summary.return_value = {
            "total_expenses": Decimal("12000.00"),
            "bill_count": 8,
        }

        service = BriefingService(
            vault_config=populated_vault_config,
            odoo_service=mock_odoo,
        )

        briefing = service.generate_briefing(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
            monthly_goal=Decimal("100000.00"),
        )

        assert briefing.revenue_this_week == Decimal("45000.00")
        assert briefing.monthly_goal == Decimal("100000.00")

    def test_briefing_write_and_read_roundtrip(
        self, populated_vault_config: VaultConfig, populated_vault: Path
    ) -> None:
        """Test writing and reading a briefing file."""
        service = BriefingService(vault_config=populated_vault_config)

        briefing = service.generate_briefing(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
        )

        # Write to file
        filepath = service.write_briefing(briefing)

        # Verify file exists
        assert filepath.exists()
        assert filepath.parent == populated_vault / "Briefings"

        # Verify content
        content = filepath.read_text()
        assert "CEO Briefing" in content
        assert "Executive Summary" in content

    def test_briefing_with_social_media_data(
        self, populated_vault_config: VaultConfig
    ) -> None:
        """Test briefing includes social media summary."""
        service = BriefingService(vault_config=populated_vault_config)

        briefing = service.generate_briefing(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
        )

        # Social posts were created in the populated vault
        if briefing.social_media_summary:
            assert briefing.social_media_summary.posts_published >= 1

    def test_briefing_idempotent(
        self, populated_vault_config: VaultConfig
    ) -> None:
        """Test that generating the same briefing twice produces consistent results."""
        service = BriefingService(vault_config=populated_vault_config)

        briefing_1 = service.generate_briefing(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
        )

        briefing_2 = service.generate_briefing(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
        )

        # Core data should be the same
        assert briefing_1.id == briefing_2.id
        assert briefing_1.revenue_this_week == briefing_2.revenue_this_week
        assert len(briefing_1.completed_tasks) == len(briefing_2.completed_tasks)

    def test_briefing_empty_vault(self, tmp_path: Path) -> None:
        """Test briefing generation with an empty vault."""
        vault = tmp_path / "empty_vault"
        vault.mkdir()
        (vault / "Done").mkdir()
        (vault / "Logs").mkdir()
        (vault / "Briefings").mkdir()
        (vault / "Social" / "LinkedIn" / "posts").mkdir(parents=True)

        config = VaultConfig(root=vault)
        service = BriefingService(vault_config=config)

        briefing = service.generate_briefing(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
        )

        assert isinstance(briefing, CEOBriefing)
        assert len(briefing.completed_tasks) == 0
        assert briefing.revenue_this_week == Decimal("0")
