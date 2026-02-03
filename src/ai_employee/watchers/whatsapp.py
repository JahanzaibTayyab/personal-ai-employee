"""WhatsApp Watcher - monitors WhatsApp Web for urgent messages.

Uses Playwright for browser automation to monitor WhatsApp Web.
Detects messages with configurable keywords and creates action items.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from ai_employee.config import VaultConfig
from ai_employee.models.watcher_event import EventType, SourceType, WatcherEvent
from ai_employee.models.whatsapp_message import (
    DEFAULT_KEYWORDS,
    WhatsAppMessage,
)
from ai_employee.utils.frontmatter import generate_frontmatter
from ai_employee.watchers.base import BaseWatcher


class WhatsAppWatcherStatus(str, Enum):
    """Status of the WhatsApp watcher connection."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    QR_REQUIRED = "qr_required"
    CONNECTED = "connected"
    SESSION_EXPIRED = "session_expired"
    ERROR = "error"


def parse_whatsapp_message(
    raw_data: dict[str, Any],
    keywords: list[str] | None = None,
) -> WhatsAppMessage | None:
    """Parse raw WhatsApp message data into WhatsAppMessage.

    Args:
        raw_data: Dictionary with sender, content, timestamp, chat_name
        keywords: Optional custom keyword list for detection

    Returns:
        WhatsAppMessage if keywords matched, None otherwise
    """
    content = raw_data.get("content", "")
    sender = raw_data.get("sender", "Unknown")
    chat_name = raw_data.get("chat_name")

    # Detect keywords in content
    matched_keywords = WhatsAppMessage.detect_keywords(content, keywords)

    if not matched_keywords:
        return None

    # Check if sender looks like a phone number
    phone_number = None
    if sender and re.match(r"^\+?[\d\s\-()]+$", sender):
        phone_number = sender

    return WhatsAppMessage.create(
        sender=sender,
        content=content,
        keywords=matched_keywords,
        chat_name=chat_name,
        phone_number=phone_number,
    )


class WhatsAppWatcher(BaseWatcher):
    """Watches WhatsApp Web for urgent messages using Playwright.

    Features:
    - Keyword-based message filtering (FR-007)
    - Persistent browser session to avoid repeated QR scans (FR-010)
    - Session expiration detection (FR-009)
    - Heartbeat logging for uptime tracking (SC-007)
    """

    SESSION_TIMEOUT_HOURS = 24  # Session expires after 24 hours of inactivity
    HEARTBEAT_INTERVAL = 60  # Seconds between heartbeat logs

    def __init__(
        self,
        vault_config: VaultConfig,
        keywords: list[str] | None = None,
        session_dir: Path | None = None,
    ) -> None:
        """Initialize the WhatsApp watcher.

        Args:
            vault_config: Vault configuration with paths
            keywords: Custom keyword list (defaults to DEFAULT_KEYWORDS)
            session_dir: Custom session storage directory
        """
        super().__init__(vault_config.root, SourceType.WHATSAPP)
        self._config = vault_config
        self.keywords = keywords or list(DEFAULT_KEYWORDS)
        self.status = WhatsAppWatcherStatus.DISCONNECTED

        # Session storage for persistent login (FR-010)
        if session_dir:
            self._session_path = session_dir
        else:
            self._session_path = vault_config.root / ".whatsapp_session"

        # Activity tracking for session expiration (FR-009)
        self._last_activity = datetime.now()
        self._last_heartbeat = datetime.now()

        # Playwright browser instance
        self._browser = None
        self._page = None

        # Callbacks for external consumers
        self.on_message_detected: Callable[[WhatsAppMessage], None] | None = None
        self.on_status_change: Callable[[WhatsAppWatcherStatus], None] | None = None

    @property
    def session_path(self) -> Path:
        """Get the session storage path."""
        return self._session_path

    def get_whatsapp_folder(self) -> Path:
        """Get the WhatsApp action items folder."""
        return self._config.needs_action_whatsapp

    def set_status(self, new_status: WhatsAppWatcherStatus) -> None:
        """Update watcher status and notify listeners."""
        old_status = self.status
        self.status = new_status

        if old_status != new_status:
            self.log_event(
                EventType.DETECTED,
                "whatsapp_status",
                {"old_status": old_status.value, "new_status": new_status.value},
            )

            if self.on_status_change:
                self.on_status_change(new_status)

    def is_session_expired(self) -> bool:
        """Check if the session has expired due to inactivity."""
        if self._last_activity is None:
            return True

        expiry_time = self._last_activity + timedelta(hours=self.SESSION_TIMEOUT_HOURS)
        return datetime.now() > expiry_time

    def log_heartbeat(self) -> None:
        """Log a heartbeat for uptime tracking (SC-007)."""
        now = datetime.now()
        if (now - self._last_heartbeat).total_seconds() >= self.HEARTBEAT_INTERVAL:
            self.log_event(
                EventType.DETECTED,
                "whatsapp_heartbeat",
                {
                    "status": self.status.value,
                    "uptime_seconds": (now - self._last_activity).total_seconds()
                    if self._last_activity
                    else 0,
                },
            )
            self._last_heartbeat = now

    def create_action_file(self, message: WhatsAppMessage) -> Path:
        """Create action file for detected urgent message (FR-008).

        Args:
            message: The detected WhatsApp message

        Returns:
            Path to created action file
        """
        folder = self.get_whatsapp_folder()
        folder.mkdir(parents=True, exist_ok=True)

        file_path = folder / message.get_filename()

        # Build body content
        body_lines = [
            f"# WhatsApp Message from {message.sender}",
            "",
            f"**Received**: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Keywords**: {', '.join(message.keywords)}",
        ]

        if message.chat_name:
            body_lines.append(f"**Chat**: {message.chat_name}")

        body_lines.extend([
            "",
            "## Message",
            "",
            message.content,
            "",
            "---",
            "*Detected by WhatsApp Watcher*",
        ])

        body = "\n".join(body_lines)
        content = generate_frontmatter(message.to_frontmatter(), body)

        file_path.write_text(content)

        self.log_event(
            EventType.CREATED,
            message.id,
            {
                "sender": message.sender,
                "keywords": message.keywords,
                "file": str(file_path),
            },
        )

        if self.on_message_detected:
            self.on_message_detected(message)

        return file_path

    def _update_activity(self) -> None:
        """Update last activity timestamp."""
        self._last_activity = datetime.now()

    async def _init_browser(self) -> None:
        """Initialize Playwright browser with persistent session."""
        try:
            from playwright.async_api import async_playwright

            self.set_status(WhatsAppWatcherStatus.CONNECTING)

            playwright = await async_playwright().start()

            # Use persistent context to maintain session (FR-010)
            self._session_path.mkdir(parents=True, exist_ok=True)

            self._browser = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(self._session_path),
                headless=False,  # WhatsApp Web requires visible browser
            )

            page = await self._browser.new_page()
            self._page = page
            await page.goto("https://web.whatsapp.com")

            # Wait for either QR code or chat list
            try:
                await page.wait_for_selector(
                    '[data-testid="qrcode"], [data-testid="chat-list"]',
                    timeout=30000,
                )

                # Check if QR code is visible
                qr_element = await page.query_selector('[data-testid="qrcode"]')
                if qr_element:
                    self.set_status(WhatsAppWatcherStatus.QR_REQUIRED)
                    print("Please scan the QR code to log in...")

                    # Wait for login to complete
                    await page.wait_for_selector(
                        '[data-testid="chat-list"]',
                        timeout=120000,  # 2 minutes to scan QR
                    )

                self.set_status(WhatsAppWatcherStatus.CONNECTED)
                self._update_activity()

            except Exception as e:
                self.set_status(WhatsAppWatcherStatus.ERROR)
                raise

        except ImportError:
            raise RuntimeError(
                "Playwright is not installed. Install with: uv add playwright"
            )

    async def _watch_messages(self) -> None:
        """Watch for new messages in WhatsApp Web."""
        if not self._page:
            return

        while self.running:
            try:
                # Check for session expiration
                if self.is_session_expired():
                    self.set_status(WhatsAppWatcherStatus.SESSION_EXPIRED)
                    break

                # Log heartbeat
                self.log_heartbeat()

                # Look for unread message indicators
                unread_chats = await self._page.query_selector_all(
                    '[data-testid="unread-count"]'
                )

                for chat in unread_chats:
                    # Get parent chat element
                    chat_element = await chat.evaluate_handle(
                        "el => el.closest('[data-testid=\"cell-frame-container\"]')"
                    )

                    if chat_element:
                        # Click to open chat
                        await chat_element.click()
                        await asyncio.sleep(0.5)

                        # Get messages from the chat
                        messages = await self._extract_recent_messages()

                        for msg_data in messages:
                            message = parse_whatsapp_message(msg_data, self.keywords)
                            if message:
                                self.create_action_file(message)
                                self._update_activity()

                await asyncio.sleep(5)  # Poll interval

            except Exception as e:
                self.log_event(
                    EventType.ERROR,
                    "whatsapp_watch_error",
                    {"error": str(e)},
                )
                await asyncio.sleep(10)

    async def _extract_recent_messages(self) -> list[dict[str, Any]]:
        """Extract recent messages from current chat."""
        if not self._page:
            return []

        messages = []

        try:
            # Get chat header for chat name
            chat_header = await self._page.query_selector(
                '[data-testid="conversation-header"] span[title]'
            )
            chat_name = None
            if chat_header:
                chat_name = await chat_header.get_attribute("title")

            # Get message bubbles
            msg_elements = await self._page.query_selector_all(
                '[data-testid="msg-container"]'
            )

            for msg_el in msg_elements[-10:]:  # Last 10 messages
                try:
                    # Check if incoming message (not sent by us)
                    is_incoming = await msg_el.query_selector('[data-testid="msg-text"]')

                    if is_incoming:
                        content_el = await msg_el.query_selector(
                            '[data-testid="msg-text"] span'
                        )
                        sender_el = await msg_el.query_selector(
                            '[data-testid="author"]'
                        )
                        time_el = await msg_el.query_selector(
                            '[data-testid="msg-meta"] span'
                        )

                        content = ""
                        if content_el:
                            content = await content_el.inner_text()

                        sender = "Unknown"
                        if sender_el:
                            sender = await sender_el.inner_text()
                        elif chat_name:
                            sender = chat_name

                        timestamp = ""
                        if time_el:
                            timestamp = await time_el.inner_text()

                        if content:
                            messages.append({
                                "sender": sender,
                                "content": content,
                                "timestamp": timestamp,
                                "chat_name": chat_name,
                            })

                except Exception:
                    continue

        except Exception as e:
            self.log_event(
                EventType.ERROR,
                "message_extraction_error",
                {"error": str(e)},
            )

        return messages

    def start(self) -> None:
        """Start the WhatsApp watcher."""
        if self.running:
            return

        self.running = True

        self.log_event(
            EventType.STARTED,
            "whatsapp_watcher",
            {"keywords": self.keywords},
        )

        # Run async event loop
        try:
            asyncio.run(self._run_async())
        except KeyboardInterrupt:
            self.stop()

    async def _run_async(self) -> None:
        """Run the async watcher loop."""
        await self._init_browser()
        await self._watch_messages()

    def stop(self) -> None:
        """Stop the WhatsApp watcher."""
        if not self.running:
            return

        self.running = False
        self.set_status(WhatsAppWatcherStatus.DISCONNECTED)

        # Close browser
        if self._browser:
            asyncio.run(self._browser.close())
            self._browser = None
            self._page = None

        self.log_event(
            EventType.STOPPED,
            "whatsapp_watcher",
            {},
        )

    def process_event(self, event: WatcherEvent) -> None:
        """Process a detected event."""
        # Events are processed through callbacks
        pass


def run_whatsapp_watcher(
    vault_path: Path,
    keywords: list[str] | None = None,
    poll_interval: int = 5,
) -> None:
    """Run the WhatsApp watcher.

    Args:
        vault_path: Path to the Obsidian vault
        keywords: Optional custom keyword list
        poll_interval: Seconds between message checks
    """
    from ai_employee.config import VaultConfig

    config = VaultConfig(root=vault_path)
    watcher = WhatsAppWatcher(config, keywords=keywords)

    def on_message(message: WhatsAppMessage) -> None:
        print(f"[DETECTED] {message.sender}: {message.content[:50]}...")
        print(f"           Keywords: {', '.join(message.keywords)}")

    def on_status(status: WhatsAppWatcherStatus) -> None:
        print(f"[STATUS] {status.value}")

    watcher.on_message_detected = on_message
    watcher.on_status_change = on_status

    try:
        watcher.start()
    except KeyboardInterrupt:
        print("\nStopping WhatsApp watcher...")
        watcher.stop()
