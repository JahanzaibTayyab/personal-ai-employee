# WhatsApp Watcher Contract

**Service**: `WhatsAppWatcher`
**Module**: `src/ai_employee/watchers/whatsapp.py`

## Overview

The WhatsApp Watcher monitors WhatsApp Web for urgent messages using Playwright browser automation. It detects messages containing configured keywords and creates action items.

## Interface

```python
from pathlib import Path
from ai_employee.models.whatsapp_message import WhatsAppMessage
from ai_employee.watchers.base import BaseWatcher

class WhatsAppWatcher(BaseWatcher):
    """Playwright-based WhatsApp Web message monitor (FR-006 to FR-010)."""

    # Default keywords (FR-007)
    DEFAULT_KEYWORDS = [
        "urgent", "asap", "invoice", "payment", "help", "pricing"
    ]

    def __init__(
        self,
        vault_path: Path,
        keywords: list[str] | None = None,
        auth_state_path: Path | None = None,
        headless: bool = True,
    ) -> None:
        """
        Initialize WhatsApp watcher.

        Args:
            vault_path: Path to Obsidian vault
            keywords: Custom keywords to detect (default: DEFAULT_KEYWORDS)
            auth_state_path: Path to Playwright auth state JSON
            headless: Run browser in headless mode (default: True)
        """

    # ─────────────────────────────────────────────────────────────
    # Session Management (FR-010)
    # ─────────────────────────────────────────────────────────────

    async def initialize_session(self) -> bool:
        """
        Initialize WhatsApp Web session.

        Returns:
            True if session restored from saved state

        Side Effects:
            - Launches browser
            - Restores auth state if available
            - Navigates to WhatsApp Web

        Note:
            If no saved state, user must scan QR code manually.
            After successful login, call save_session().
        """

    async def save_session(self) -> None:
        """
        Save current browser session state (FR-010).

        Side Effects:
            - Saves cookies, localStorage, IndexedDB to auth_state_path
            - Enables session persistence across restarts
        """

    async def check_session_valid(self) -> bool:
        """
        Check if WhatsApp session is still authenticated.

        Returns:
            True if logged in and session valid
        """

    # ─────────────────────────────────────────────────────────────
    # Monitoring (FR-006, FR-007)
    # ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """
        Start watching for new messages (FR-006).

        Side Effects:
            - Begins polling for new messages
            - Creates action items for keyword matches
            - Logs detected messages

        Raises:
            SessionExpiredError: If session invalid
        """

    async def stop(self) -> None:
        """
        Stop watching and close browser.

        Side Effects:
            - Saves session state
            - Closes browser gracefully
        """

    async def scan_messages(self) -> list[WhatsAppMessage]:
        """
        Scan recent messages for keyword matches (FR-007).

        Returns:
            List of messages containing keywords

        Note:
            Scans unread messages across all chats.
            Messages already processed are skipped.
        """

    def matches_keywords(self, content: str) -> list[str]:
        """
        Check if message content matches configured keywords.

        Args:
            content: Message text content

        Returns:
            List of matched keywords (empty if no match)
        """

    # ─────────────────────────────────────────────────────────────
    # Action Item Creation (FR-008)
    # ─────────────────────────────────────────────────────────────

    def create_action_item(
        self,
        message: WhatsAppMessage,
    ) -> Path:
        """
        Create action item file for detected message (FR-008).

        Args:
            message: Detected WhatsApp message

        Returns:
            Path to created action item file

        Side Effects:
            - Creates markdown file in /Needs_Action/WhatsApp/
            - Includes: sender, content, timestamp, keywords
        """

    # ─────────────────────────────────────────────────────────────
    # Session Expiration Handling (FR-009)
    # ─────────────────────────────────────────────────────────────

    async def handle_session_expired(self) -> None:
        """
        Handle WhatsApp session expiration (FR-009).

        Side Effects:
            - Pauses monitoring
            - Updates Dashboard with session expired alert
            - Logs session expiration event

        Note:
            User must re-authenticate by scanning QR code
            or by restoring valid session state.
        """
```

## Session State File

```json
// playwright/.auth/whatsapp.json
{
  "cookies": [
    {
      "name": "wa_lang_pref",
      "value": "en",
      "domain": ".whatsapp.com",
      "path": "/",
      "expires": 1738000000,
      "httpOnly": false,
      "secure": true
    }
  ],
  "origins": [
    {
      "origin": "https://web.whatsapp.com",
      "localStorage": [
        {
          "name": "last-wid",
          "value": "user_id_here"
        }
      ]
    }
  ]
}
```

## Message Detection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     WhatsApp Web Browser                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    scan_messages()
                             │
                             ▼
                    ┌────────────────┐
                    │ Get unread     │
                    │ message list   │
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ For each msg:  │
                    │ check keywords │
                    └────────┬───────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
        Keywords match?               No match
              │                             │
              ▼                             ▼
    ┌─────────────────┐              (skip message)
    │ Create action   │
    │ item in vault   │
    └────────┬────────┘
             │
             ▼
    /Needs_Action/WhatsApp/WHATSAPP_20260203_143022.md
```

## Error Handling

```python
class WhatsAppError(Exception):
    """Base exception for WhatsApp watcher."""

class SessionExpiredError(WhatsAppError):
    """Raised when WhatsApp session is invalid or expired."""

class SessionInitError(WhatsAppError):
    """Raised when session initialization fails."""

class BrowserError(WhatsAppError):
    """Raised when browser automation fails."""
```

## Configuration

```python
# Default configuration
WHATSAPP_CONFIG = {
    "poll_interval_seconds": 30,
    "keywords": [
        "urgent", "asap", "invoice",
        "payment", "help", "pricing"
    ],
    "auth_state_path": "playwright/.auth/whatsapp.json",
    "headless": True,
    "timeout_ms": 30000,
    "duplicate_window_minutes": 5,  # Prevent duplicate action items
}
```

## Events & Logging

| Event | Log Level | Details |
|-------|-----------|---------|
| Session initialized | INFO | restored_from_state (bool) |
| Session saved | INFO | state_path |
| Session expired | WARNING | last_valid_time |
| Message detected | INFO | sender, keywords, timestamp |
| Action item created | INFO | file_path, message_id |
| Scan completed | DEBUG | messages_scanned, matches_found |
| Browser error | ERROR | error_message, page_url |
