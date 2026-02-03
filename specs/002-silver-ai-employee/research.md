# Silver Tier AI Employee - Technology Research

**Created**: 2026-02-03 | **Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

## Executive Summary

Research on five key technologies for Silver Tier implementation: Playwright for WhatsApp automation, LinkedIn Official API, Google Workspace MCP, task scheduling, and browser session persistence.

---

## 1. WhatsApp Automation - Playwright

### Decision
**Use Playwright Python with persistent browser contexts for WhatsApp Web monitoring**

### Rationale
- Official Playwright Python has proven authentication and session persistence patterns
- Async/await support enables efficient concurrent operations
- Supports local storage, cookies, and IndexedDB state persistence
- Compatible with existing Python infrastructure

### Alternatives Considered
| Option | Rejected Because |
|--------|------------------|
| Selenium | Lacks async support, heavier resource footprint |
| Puppeteer-python | Less mature Python bindings |
| WhatsApp Business API | Requires business verification, not for personal accounts |

### Key Implementation Patterns
```python
# Save authentication state after QR code scan
await context.storage_state(path="playwright/.auth/whatsapp.json")

# Restore state on subsequent runs
context = await browser.new_context(storage_state="playwright/.auth/whatsapp.json")
```

### Gotchas
- QR code scanning requires manual confirmation on first setup
- WhatsApp actively detects bots - implement random delays (500-3000ms)
- Session may expire; need reconnection logic and Dashboard alerts

---

## 2. LinkedIn Integration - Official API

### Decision
**Use `linkedin-api-client` (Official Python Client) from PyPI**

### Rationale
- Official package maintained by LinkedIn at `linkedin-developers/linkedin-api-python-client`
- Supports 3-legged OAuth2 for user-delegated posting
- Handles Rest.li protocol complexity
- Published on PyPI: `uv add linkedin-api-client`

### Alternatives Considered
| Option | Rejected Because |
|--------|------------------|
| python-linkedin | Unmaintained, lacks modern OAuth2 |
| Unofficial scraping libraries | Violate ToS, high ban risk |
| Browser automation | Unreliable, maintenance burden |

### Key Implementation Patterns
```python
from linkedin_api_client.auth import AuthClient
from linkedin_api_client.restli import RestliClient

auth_client = AuthClient(
    client_id=os.environ["LINKEDIN_CLIENT_ID"],
    client_secret=os.environ["LINKEDIN_CLIENT_SECRET"],
    redirect_url="http://localhost:8000/callback"
)

# OAuth flow for user authorization
auth_url = auth_client.get_authorization_url(scopes=["w_member_social"])
access_token = auth_client.exchange_authorization_code(code)

# Post to profile
restli_client = RestliClient(access_token)
restli_client.create("rest/posts", {"text": "Post content"})
```

### Gotchas
- **Highly Restricted Access**: Requires LinkedIn partnership for advanced features
- **Rate Limiting**: Subject to LinkedIn's rate limits (max 25 posts/day per spec)
- **No DM/Comment APIs**: Limited to basic post creation
- **Beta Status**: API subject to change

---

## 3. Gmail Integration - Google Workspace MCP

### Decision
**Use `workspace-mcp` package for Gmail operations**

### Rationale
- Most feature-complete Google Workspace MCP (1,283 stars)
- Supports Gmail: read, send, manage threads and labels
- OAuth2.1 with automatic token refresh
- Compatible with Claude Code MCP server infrastructure
- Installation: `uv add workspace-mcp`

### Alternatives Considered
| Option | Rejected Because |
|--------|------------------|
| Custom Email MCP | More work, same functionality |
| mcp-google-suite | Less complete, Gmail-specific features limited |
| Direct Gmail API | More integration work, no MCP benefits |

### Key Implementation Patterns
```bash
# Environment configuration
export GOOGLE_CLIENT_ID="your_client_id"
export GOOGLE_CLIENT_SECRET="your_client_secret"
export GOOGLE_REDIRECT_URI="http://localhost:8080/callback"

# Run MCP server for Gmail
uvx workspace-mcp --tools gmail
```

### MCP Configuration for Claude Code
```json
{
  "mcpServers": {
    "workspace": {
      "command": "uvx",
      "args": ["workspace-mcp", "--tools", "gmail"]
    }
  }
}
```

### Gotchas
- Requires Google Cloud Console OAuth consent screen setup
- Must request appropriate OAuth scopes (`https://www.googleapis.com/auth/gmail.send`)
- Subject to Google Workspace API quotas

---

## 4. Task Scheduling - APScheduler

### Decision
**Use APScheduler for production scheduling with file-based job storage**

### Rationale
- Supports persistent job storage (survives service restarts)
- Multiple scheduling triggers: cron expressions, intervals, one-time
- Production-grade with ThreadPoolExecutor support
- Installation: `uv add apscheduler`

### Alternatives Considered
| Option | Rejected Because |
|--------|------------------|
| schedule library | No job persistence, single-threaded |
| System cron | Platform-specific, harder to manage programmatically |
| Celery Beat | Over-engineering for single-user system |

### Key Implementation Patterns
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# For Silver tier: Use SQLite for simplicity (file-based, matches vault pattern)
job_stores = {
    'default': SQLAlchemyJobStore(url='sqlite:///vault/schedules/jobs.db')
}

scheduler = BackgroundScheduler(
    jobstores=job_stores,
    job_defaults={'coalesce': True, 'max_instances': 1}
)

# Daily briefing at 8:00 AM
scheduler.add_job(
    generate_daily_briefing,
    'cron',
    hour=8,
    minute=0,
    id='daily_briefing',
    misfire_grace_time=600  # 10 minutes
)

# Weekly audit on Sunday 9:00 PM
scheduler.add_job(
    generate_weekly_audit,
    'cron',
    day_of_week='sun',
    hour=21,
    id='weekly_audit'
)

scheduler.start()
```

### Missed Schedule Handling
```python
# Configuration options per spec FR-029:
job_defaults = {
    'coalesce': True,        # Combine missed runs into one
    'max_instances': 1,      # Prevent overlapping
    'misfire_grace_time': 600  # 10 minutes grace period
}
```

### Gotchas
- Job serialization uses pickle (avoid untrusted data)
- Requires explicit scheduler lifecycle management
- SQLite file locking may cause issues if multiple processes access

---

## 5. Browser Session Persistence

### Decision
**Use Playwright's `storage_state()` with secure file storage**

### Rationale
- Official Playwright approach for session persistence
- Persists cookies, local storage, and IndexedDB
- Eliminates repeated QR code scans for WhatsApp
- JSON format allows inspection and debugging

### Implementation Pattern
```python
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

AUTH_DIR = Path("playwright/.auth")
WHATSAPP_STATE = AUTH_DIR / "whatsapp.json"

async def save_whatsapp_session():
    """Initial setup: Save auth state after QR scan."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto('https://web.whatsapp.com')

        # Wait for QR scan completion
        await page.wait_for_selector(
            '[data-testid="conversation-panel-wrapper"]',
            timeout=120000  # 2 minutes for manual scan
        )

        # Save authenticated state
        AUTH_DIR.mkdir(parents=True, exist_ok=True)
        await context.storage_state(path=str(WHATSAPP_STATE))
        await browser.close()

async def restore_whatsapp_session():
    """Subsequent runs: Restore saved session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Restore authentication state
        context = await browser.new_context(
            storage_state=str(WHATSAPP_STATE)
        )
        page = await context.new_page()
        await page.goto('https://web.whatsapp.com')

        return browser, context, page
```

### Security Best Practices
```bash
# .gitignore additions
playwright/.auth/
*.json
!playwright/.auth/.gitkeep
```

```python
# File permission restriction
import os
os.chmod(WHATSAPP_STATE, 0o600)  # Owner read/write only
```

### Session Health Monitoring
```python
async def check_session_valid(context) -> bool:
    """Verify session cookies haven't expired."""
    import time
    cookies = await context.cookies()

    for cookie in cookies:
        if cookie.get('expires', float('inf')) < time.time():
            return False
    return bool(cookies)
```

### Gotchas
- WhatsApp may require periodic re-authentication for security
- State format may change with browser updates
- Cookies have expiration dates that need monitoring

---

## Dependency Summary

```toml
# pyproject.toml additions for Silver Tier
dependencies = [
    # Existing Bronze dependencies...
    "playwright>=1.40",           # WhatsApp automation
    "linkedin-api-client>=0.3",   # LinkedIn Official API
    "workspace-mcp>=0.1",         # Gmail MCP
    "apscheduler>=3.10",          # Task scheduling
    "sqlalchemy>=2.0",            # APScheduler persistence
]
```

```bash
# Installation
uv add playwright linkedin-api-client workspace-mcp apscheduler sqlalchemy

# Playwright browser installation
uv run playwright install chromium
```

---

## Environment Variables

```bash
# .env file (gitignored)

# LinkedIn OAuth2
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret

# Google Workspace
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8080/callback

# Vault path
VAULT_PATH=~/AI_Employee_Vault
```

---

## Technology Compatibility Matrix

| Technology | Python Version | Status | Notes |
|------------|---------------|--------|-------|
| Playwright | 3.8+ | ✅ Compatible | Async support |
| linkedin-api-client | 3.7+ | ✅ Compatible | Beta, official |
| workspace-mcp | 3.10+ | ✅ Compatible | Active development |
| APScheduler | 3.8+ | ✅ Compatible | Stable, production-ready |

All technologies are compatible with Python 3.13+ and can coexist using UV package manager.
