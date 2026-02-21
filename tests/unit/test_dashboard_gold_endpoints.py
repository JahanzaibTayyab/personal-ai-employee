"""Unit tests for Gold tier dashboard endpoints."""

import json
import pytest
from pathlib import Path


class TestGoldTierRoutes:
    """Test that Gold tier routes exist."""

    def test_gold_routes_registered(self):
        """Gold tier routes should be registered."""
        from ai_employee.dashboard.server import app

        routes = [r.path for r in app.routes]
        assert "/api/tasks" in routes
        assert "/api/tasks/{task_id}/pause" in routes
        assert "/api/tasks/{task_id}/resume" in routes
        assert "/api/briefings" in routes
        assert "/api/briefings/generate" in routes
        assert "/api/social/meta" in routes
        assert "/api/social/meta/{post_id}/publish" in routes
        assert "/api/social/twitter" in routes
        assert "/api/social/twitter/{tweet_id}/publish" in routes
        assert "/api/invoices" in routes
        assert "/api/health" in routes
        assert "/api/audit" in routes
        assert "/api/correlations/search" in routes


class TestGoldTierEndpoints:
    """Test Gold tier API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from ai_employee.dashboard.server import app

        return TestClient(app)

    @pytest.fixture
    def gold_vault(self, tmp_path):
        """Create mock vault with Gold tier folders."""
        vault = tmp_path / "vault"
        vault.mkdir()
        for folder in [
            "Inbox", "Needs_Action", "Done", "Quarantine", "Logs",
            "Pending_Approval", "Approved", "Rejected", "Plans",
            "Briefings", "Schedules", "Active_Tasks",
            "Accounting/invoices", "Accounting/payments",
            "Social/Meta/posts", "Social/Twitter/tweets",
            "Archive",
        ]:
            (vault / folder).mkdir(parents=True, exist_ok=True)
        return vault

    # ─── Tasks ───

    def test_get_tasks_empty(self, client, gold_vault, monkeypatch):
        """Tasks endpoint returns empty list when no tasks."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["tasks"] == []

    def test_get_tasks_with_data(self, client, gold_vault, monkeypatch):
        """Tasks endpoint returns task data from JSON files."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))

        task_data = {
            "task_id": "test_123",
            "prompt": "Process inbox items",
            "status": "running",
            "iteration": 3,
            "max_iterations": 10,
            "created_at": "2026-02-21T10:00:00",
        }
        (gold_vault / "Active_Tasks" / "test_123.json").write_text(
            json.dumps(task_data)
        )

        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["tasks"][0]["id"] == "test_123"
        assert data["tasks"][0]["status"] == "running"

    def test_create_task_missing_prompt(self, client, gold_vault, monkeypatch):
        """Create task requires prompt."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.post("/api/tasks", json={"prompt": ""})
        assert response.status_code == 400

    # ─── Briefings ───

    def test_get_briefings_empty(self, client, gold_vault, monkeypatch):
        """Briefings endpoint returns empty list."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.get("/api/briefings")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_get_briefings_with_data(self, client, gold_vault, monkeypatch):
        """Briefings endpoint returns briefing data."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))

        briefing = "---\ngenerated: 2026-02-21T07:00:00\nperiod: 2026-02-14 to 2026-02-20\n---\n# CEO Briefing\nRevenue up 10%."
        (gold_vault / "Briefings" / "2026-02-21_Monday_Briefing.md").write_text(
            briefing
        )

        response = client.get("/api/briefings")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert "Monday_Briefing" in data["briefings"][0]["filename"]

    # ─── Meta Posts ───

    def test_get_meta_posts_empty(self, client, gold_vault, monkeypatch):
        """Meta posts endpoint returns empty list."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.get("/api/social/meta")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_create_meta_post(self, client, gold_vault, monkeypatch):
        """Create meta post saves to vault."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.post("/api/social/meta", json={
            "content": "Hello from AI Employee!",
            "platform": "facebook",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["platform"] == "facebook"

    def test_create_meta_post_missing_content(self, client, gold_vault, monkeypatch):
        """Create meta post requires content."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.post("/api/social/meta", json={"content": ""})
        assert response.status_code == 400

    def test_publish_meta_post_no_credentials(self, client, gold_vault, monkeypatch):
        """Publish returns 503 without Meta credentials."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        monkeypatch.delenv("META_APP_ID", raising=False)
        response = client.post("/api/social/meta/fake_id/publish")
        assert response.status_code == 503

    # ─── Tweets ───

    def test_get_tweets_empty(self, client, gold_vault, monkeypatch):
        """Tweets endpoint returns empty list."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.get("/api/social/twitter")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_create_tweet(self, client, gold_vault, monkeypatch):
        """Create tweet saves to vault."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.post("/api/social/twitter", json={
            "content": "AI Employee tweeting!",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_tweet_missing_content(self, client, gold_vault, monkeypatch):
        """Create tweet requires content."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.post("/api/social/twitter", json={"content": ""})
        assert response.status_code == 400

    def test_publish_tweet_no_credentials(self, client, gold_vault, monkeypatch):
        """Publish returns 503 without Twitter credentials."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        monkeypatch.delenv("TWITTER_API_KEY", raising=False)
        response = client.post("/api/social/twitter/fake_id/publish")
        assert response.status_code == 503

    # ─── Invoices ───

    def test_get_invoices_empty(self, client, gold_vault, monkeypatch):
        """Invoices endpoint returns empty list."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.get("/api/invoices")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_create_invoice_returns_503(self, client, gold_vault, monkeypatch):
        """Create invoice returns 503 (Odoo required)."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.post("/api/invoices", json={})
        assert response.status_code == 503

    # ─── Health ───

    def test_health_endpoint(self, client, gold_vault, monkeypatch):
        """Health endpoint returns service statuses."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "services" in data
        assert "vault" in data["services"]

    def test_health_shows_dev_mode(self, client, gold_vault, monkeypatch):
        """Health endpoint shows dev mode status."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        monkeypatch.setenv("DEV_MODE", "true")
        response = client.get("/api/health")
        data = response.json()
        assert data["dev_mode"] is True

    # ─── Audit ───

    def test_audit_endpoint_empty(self, client, gold_vault, monkeypatch):
        """Audit endpoint returns empty when no logs."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_audit_endpoint_with_data(self, client, gold_vault, monkeypatch):
        """Audit endpoint returns entries from JSONL files."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))

        entry = {"timestamp": "2026-02-21T10:00:00", "action_type": "email_send", "result": "success"}
        (gold_vault / "Logs" / "audit_2026-02-21.jsonl").write_text(
            json.dumps(entry) + "\n"
        )

        response = client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["entries"][0]["action_type"] == "email_send"

    # ─── Correlations Search ───

    def test_search_empty_query(self, client, gold_vault, monkeypatch):
        """Search with empty query returns empty results."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.get("/api/correlations/search?q=")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_search_finds_match(self, client, gold_vault, monkeypatch):
        """Search finds matching content across vault."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))

        (gold_vault / "Done" / "test_item.md").write_text(
            "---\nid: test_123\n---\nInvoice for Client Alpha"
        )

        response = client.get("/api/correlations/search?q=Client Alpha")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["folder"] == "Done"

    def test_search_no_match(self, client, gold_vault, monkeypatch):
        """Search returns empty when no match."""
        monkeypatch.setenv("VAULT_PATH", str(gold_vault))
        response = client.get("/api/correlations/search?q=nonexistent_xyz")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0


class TestMCPConfigs:
    """Test new MCP configuration modules."""

    def test_browser_config_import(self):
        """Browser MCP config should be importable."""
        from ai_employee.mcp.browser_config import BrowserMCPConfig
        config = BrowserMCPConfig()
        assert config.headless is True
        assert config.timeout == 30

    def test_browser_config_from_env(self, monkeypatch):
        """Browser config loads from environment."""
        monkeypatch.setenv("BROWSER_HEADLESS", "false")
        monkeypatch.setenv("BROWSER_TIMEOUT", "60")

        from ai_employee.mcp.browser_config import BrowserMCPConfig
        config = BrowserMCPConfig.from_env()
        assert config.headless is False
        assert config.timeout == 60

    def test_browser_config_mcp_server(self):
        """Browser config generates MCP server JSON."""
        from ai_employee.mcp.browser_config import BrowserMCPConfig
        config = BrowserMCPConfig()
        server = config.to_mcp_server_config()
        assert server["name"] == "browser"
        assert "npx" in server["command"]

    def test_calendar_config_import(self):
        """Calendar MCP config should be importable."""
        from ai_employee.mcp.calendar_config import CalendarMCPConfig
        config = CalendarMCPConfig()
        assert config.calendar_id == "primary"

    def test_calendar_config_from_env(self, monkeypatch):
        """Calendar config loads from environment."""
        monkeypatch.setenv("CALENDAR_CREDENTIALS_PATH", "/path/to/creds.json")
        monkeypatch.setenv("CALENDAR_ID", "work")

        from ai_employee.mcp.calendar_config import CalendarMCPConfig
        config = CalendarMCPConfig.from_env()
        assert config.credentials_path == "/path/to/creds.json"
        assert config.calendar_id == "work"

    def test_calendar_config_mcp_server(self):
        """Calendar config generates MCP server JSON."""
        from ai_employee.mcp.calendar_config import CalendarMCPConfig
        config = CalendarMCPConfig(credentials_path="/test")
        server = config.to_mcp_server_config()
        assert server["name"] == "calendar"


class TestDevMode:
    """Test DEV_MODE configuration."""

    def test_config_has_dev_mode(self):
        """Config class should have dev_mode field."""
        from ai_employee.config import Config
        config = Config(vault=None, dev_mode=True)  # type: ignore[arg-type]
        assert config.dev_mode is True

    def test_config_dev_mode_from_env_true(self, monkeypatch, tmp_path):
        """Config.from_env reads DEV_MODE=true."""
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))

        from ai_employee.config import Config
        config = Config.from_env()
        assert config.dev_mode is True

    def test_config_dev_mode_from_env_false(self, monkeypatch, tmp_path):
        """Config.from_env reads DEV_MODE=false."""
        monkeypatch.setenv("DEV_MODE", "false")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))

        from ai_employee.config import Config
        config = Config.from_env()
        assert config.dev_mode is False

    def test_config_dev_mode_default(self, monkeypatch, tmp_path):
        """Config.from_env defaults dev_mode to False."""
        monkeypatch.delenv("DEV_MODE", raising=False)
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))

        from ai_employee.config import Config
        config = Config.from_env()
        assert config.dev_mode is False
