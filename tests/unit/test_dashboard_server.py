"""Unit tests for the dashboard server."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class TestDashboardImport:
    """Test dashboard module imports."""

    def test_import_dashboard_module(self):
        """Dashboard module should be importable."""
        from ai_employee.dashboard import app, run_server

        assert app is not None
        assert run_server is not None

    def test_app_has_routes(self):
        """App should have expected routes."""
        from ai_employee.dashboard.server import app

        routes = [r.path for r in app.routes]
        assert "/" in routes
        assert "/api/status" in routes
        assert "/api/approvals" in routes
        assert "/api/schedules" in routes
        assert "/api/plans" in routes


class TestDashboardEndpoints:
    """Test dashboard API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from ai_employee.dashboard.server import app

        return TestClient(app)

    @pytest.fixture
    def mock_vault(self, tmp_path):
        """Create mock vault structure."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "Inbox").mkdir()
        (vault / "Needs_Action").mkdir()
        (vault / "Done").mkdir()
        (vault / "Quarantine").mkdir()
        (vault / "Pending_Approval").mkdir()
        (vault / "Approved").mkdir()
        (vault / "Rejected").mkdir()
        (vault / "Logs").mkdir()
        return vault

    def test_dashboard_home(self, client):
        """Home endpoint should return HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_status_endpoint(self, client, mock_vault, monkeypatch):
        """Status endpoint should return counts."""
        monkeypatch.setenv("VAULT_PATH", str(mock_vault))

        # Create some files
        (mock_vault / "Inbox" / "test1.md").write_text("test")
        (mock_vault / "Needs_Action" / "test2.md").write_text("test")

        response = client.get("/api/status")
        assert response.status_code == 200

        data = response.json()
        assert "counts" in data
        assert "watchers" in data
        assert data["counts"]["inbox"] == 1
        assert data["counts"]["needs_action"] == 1

    def test_approvals_endpoint_empty(self, client, mock_vault, monkeypatch):
        """Approvals endpoint should return empty list when no approvals."""
        monkeypatch.setenv("VAULT_PATH", str(mock_vault))

        response = client.get("/api/approvals")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 0
        assert data["approvals"] == []

    def test_approvals_endpoint_with_approval(self, client, mock_vault, monkeypatch):
        """Approvals endpoint should return pending approvals."""
        monkeypatch.setenv("VAULT_PATH", str(mock_vault))

        # Create an approval file
        approval_file = mock_vault / "Pending_Approval" / "APPROVAL_email_test123.md"
        approval_content = """---
id: test123
category: email
status: pending
created_at: '2026-02-05T00:00:00'
expires_at: '2026-02-06T00:00:00'
payload:
  to:
  - test@example.com
  subject: Test Email
  body: Test body
---

# Approval Request: Email

**ID**: test123
"""
        approval_file.write_text(approval_content)

        response = client.get("/api/approvals")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 1
        assert data["approvals"][0]["id"] == "test123"
        assert data["approvals"][0]["category"] == "email"

    def test_schedules_endpoint(self, client, mock_vault, monkeypatch):
        """Schedules endpoint should return scheduled tasks."""
        monkeypatch.setenv("VAULT_PATH", str(mock_vault))

        response = client.get("/api/schedules")
        assert response.status_code == 200

        data = response.json()
        assert "count" in data
        assert "schedules" in data

    def test_plans_endpoint(self, client, mock_vault, monkeypatch):
        """Plans endpoint should return active plans."""
        monkeypatch.setenv("VAULT_PATH", str(mock_vault))

        response = client.get("/api/plans")
        assert response.status_code == 200

        data = response.json()
        assert "count" in data
        assert "plans" in data

    def test_approve_request(self, client, mock_vault, monkeypatch):
        """Approve endpoint should approve a request."""
        monkeypatch.setenv("VAULT_PATH", str(mock_vault))

        # Use the EmailService to create a proper approval request
        from ai_employee.config import VaultConfig
        from ai_employee.services.email import EmailService, EmailDraft

        config = VaultConfig(root=mock_vault)
        email_service = EmailService(config)

        draft = EmailDraft(
            to=["test@example.com"],
            subject="Test Email for Approval",
            body="Test body content"
        )
        approval_id = email_service.draft_email(draft)

        response = client.post(f"/api/approvals/{approval_id}/approve")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_reject_request(self, client, mock_vault, monkeypatch):
        """Reject endpoint should reject a request."""
        monkeypatch.setenv("VAULT_PATH", str(mock_vault))

        # Use the EmailService to create a proper approval request
        from ai_employee.config import VaultConfig
        from ai_employee.services.email import EmailService, EmailDraft

        config = VaultConfig(root=mock_vault)
        email_service = EmailService(config)

        draft = EmailDraft(
            to=["test@example.com"],
            subject="Test Email for Rejection",
            body="Test body content"
        )
        approval_id = email_service.draft_email(draft)

        response = client.post(f"/api/approvals/{approval_id}/reject")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_send_email_endpoint(self, client, mock_vault, monkeypatch):
        """Send email endpoint should create approval request."""
        monkeypatch.setenv("VAULT_PATH", str(mock_vault))

        response = client.post("/api/email/send", json={
            "to": ["test@example.com"],
            "subject": "Test Email",
            "body": "Test body content"
        })
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "approval_id" in response.json()

    def test_linkedin_post_endpoint(self, client, mock_vault, monkeypatch):
        """LinkedIn post endpoint should create approval request."""
        monkeypatch.setenv("VAULT_PATH", str(mock_vault))

        response = client.post("/api/linkedin/post", json={
            "content": "Test LinkedIn post content"
        })
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "approval_id" in response.json()


class TestStaticFiles:
    """Test static file serving."""

    def test_css_exists(self):
        """Dashboard CSS file should exist."""
        from pathlib import Path
        css_path = Path(__file__).parent.parent.parent / "src" / "ai_employee" / "dashboard" / "static" / "css" / "dashboard.css"
        assert css_path.exists()

    def test_js_exists(self):
        """Dashboard JS file should exist."""
        from pathlib import Path
        js_path = Path(__file__).parent.parent.parent / "src" / "ai_employee" / "dashboard" / "static" / "js" / "dashboard.js"
        assert js_path.exists()

    def test_template_exists(self):
        """Dashboard template should exist."""
        from pathlib import Path
        template_path = Path(__file__).parent.parent.parent / "src" / "ai_employee" / "dashboard" / "templates" / "dashboard.html"
        assert template_path.exists()
