"""Gmail Watcher - monitors Gmail for unread important emails."""

import base64
import json
import time
from datetime import datetime
from pathlib import Path
from threading import Thread

from ai_employee.config import VaultConfig
from ai_employee.models.action_item import (
    ActionItem,
    ActionItemStatus,
    ActionItemType,
    SourceType,
)
from ai_employee.models.watcher_event import EventType, WatcherEvent
from ai_employee.models.watcher_event import SourceType as WatcherSourceType
from ai_employee.services.handbook import detect_priority_from_text
from ai_employee.utils.frontmatter import generate_frontmatter
from ai_employee.watchers.base import BaseWatcher


class GmailWatcher(BaseWatcher):
    """Watcher for Gmail that creates action items for unread important emails."""

    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    POLL_INTERVAL = 120  # 2 minutes

    def __init__(
        self,
        vault_config: VaultConfig,
        credentials_path: Path | None = None,
        token_path: Path | None = None,
    ):
        """Initialize the Gmail watcher.

        Args:
            vault_config: Vault configuration with paths
            credentials_path: Path to OAuth2 credentials.json
            token_path: Path to store/load token.json
        """
        super().__init__(vault_config.root, WatcherSourceType.GMAIL)
        self.vault_config = vault_config
        self.credentials_path = credentials_path
        self.token_path = token_path or Path.home() / ".config" / "ai-employee" / "token.json"
        self._thread: Thread | None = None
        self._stop_flag = False
        self._service = None
        self._processed_ids: set[str] = set()
        self._processed_ids_file = vault_config.logs / "gmail_processed_ids.json"

    def _load_processed_ids(self) -> None:
        """Load previously processed message IDs from file."""
        if self._processed_ids_file.exists():
            try:
                with open(self._processed_ids_file) as f:
                    self._processed_ids = set(json.load(f))
            except (OSError, json.JSONDecodeError):
                self._processed_ids = set()

    def _save_processed_ids(self) -> None:
        """Save processed message IDs to file."""
        self._processed_ids_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._processed_ids_file, "w") as f:
            json.dump(list(self._processed_ids), f)

    def _authenticate(self) -> bool:
        """Authenticate with Gmail API.

        Returns:
            True if authentication succeeded
        """
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None

            # Load existing token
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_path), self.SCOPES)

            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.credentials_path or not self.credentials_path.exists():
                        return False
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save token
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())

            self._service = build("gmail", "v1", credentials=creds)
            return True

        except ImportError:
            print(
                "Gmail dependencies not installed. Run: "
                "uv add google-auth google-api-python-client google-auth-oauthlib --optional gmail"
            )
            return False
        except Exception as e:
            self.log_event(
                EventType.ERROR,
                "gmail_auth",
                {"error_message": str(e)}
            )
            return False

    def _fetch_unread_important(self) -> list[dict]:
        """Fetch unread important emails.

        Returns:
            List of message metadata dictionaries
        """
        if not self._service:
            return []

        try:
            # Query for unread important messages
            results = self._service.users().messages().list(
                userId="me",
                q="is:unread is:important",
                maxResults=10
            ).execute()

            messages = results.get("messages", [])
            return messages

        except Exception as e:
            self.log_event(
                EventType.ERROR,
                "gmail_fetch",
                {"error_message": str(e)}
            )
            return []

    def _get_message_details(self, message_id: str) -> dict | None:
        """Get full details of a message.

        Args:
            message_id: Gmail message ID

        Returns:
            Message details or None if failed
        """
        if not self._service:
            return None

        try:
            message = self._service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()

            # Extract headers
            headers = message.get("payload", {}).get("headers", [])
            header_dict = {h["name"].lower(): h["value"] for h in headers}

            # Extract snippet
            snippet = message.get("snippet", "")

            # Try to get body
            body = ""
            payload = message.get("payload", {})
            if "body" in payload and payload["body"].get("data"):
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
            elif "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        break

            return {
                "id": message_id,
                "from": header_dict.get("from", "Unknown"),
                "subject": header_dict.get("subject", "No Subject"),
                "date": header_dict.get("date", ""),
                "snippet": snippet,
                "body": body[:5000] if body else snippet,  # Limit body size
            }

        except Exception as e:
            self.log_event(
                EventType.ERROR,
                message_id,
                {"error_message": str(e)}
            )
            return None

    def _create_action_item(self, message: dict) -> bool:
        """Create an action item for an email.

        Args:
            message: Message details dictionary

        Returns:
            True if action item was created
        """
        try:
            message_id = message["id"]
            subject = message["subject"]
            from_address = message["from"]
            body = message.get("body", message.get("snippet", ""))

            # Create action item
            action_item = ActionItem(
                type=ActionItemType.EMAIL,
                source=SourceType.GMAIL,
                original_name=subject,
                created=datetime.now(),
                status=ActionItemStatus.PENDING,
                priority=detect_priority_from_text(f"{subject} {body}"),
                from_address=from_address,
                message_id=message_id,
            )

            # Ensure Email subfolder exists
            email_folder = self.vault_config.needs_action_email
            email_folder.mkdir(parents=True, exist_ok=True)

            # Generate content
            content = f"""## Email Details

**From**: {from_address}
**Subject**: {subject}
**Date**: {message.get('date', 'Unknown')}

## Content

{body}

## Suggested Actions

- [ ] Review email content
- [ ] Respond if needed
- [ ] Mark as done when processed
"""

            # Write action item
            filename = action_item.get_filename()
            filepath = email_folder / filename
            frontmatter = action_item.to_frontmatter()
            markdown_content = generate_frontmatter(frontmatter, content)
            filepath.write_text(markdown_content)

            # Mark as processed
            self._processed_ids.add(message_id)
            self._save_processed_ids()

            # Log event
            self.log_event(
                EventType.CREATED,
                message_id,
                {
                    "from_address": from_address,
                    "subject": subject,
                    "action_item": filename,
                }
            )

            return True

        except Exception as e:
            self.log_event(
                EventType.ERROR,
                message.get("id", "unknown"),
                {"error_message": str(e)}
            )
            return False

    def _poll_loop(self) -> None:
        """Main polling loop for Gmail."""
        while not self._stop_flag:
            try:
                messages = self._fetch_unread_important()

                for msg_meta in messages:
                    message_id = msg_meta["id"]

                    # Skip if already processed
                    if message_id in self._processed_ids:
                        continue

                    # Get full details
                    message = self._get_message_details(message_id)
                    if message:
                        self._create_action_item(message)

            except Exception as e:
                self.log_event(
                    EventType.ERROR,
                    "gmail_poll",
                    {"error_message": str(e)}
                )

            # Wait for next poll
            for _ in range(self.POLL_INTERVAL):
                if self._stop_flag:
                    break
                time.sleep(1)

    def start(self) -> None:
        """Start the Gmail watcher."""
        if self.running:
            return

        # Load processed IDs
        self._load_processed_ids()

        # Authenticate
        if not self._authenticate():
            print("Gmail authentication failed. Check credentials.")
            return

        # Start polling thread
        self._stop_flag = False
        self._thread = Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        self.running = True

        self.log_event(
            EventType.STARTED,
            "gmail",
            {"message": "Gmail watcher started"}
        )

    def stop(self) -> None:
        """Stop the Gmail watcher."""
        if not self.running:
            return

        self._stop_flag = True
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

        self.running = False

        self.log_event(
            EventType.STOPPED,
            "gmail",
            {"message": "Gmail watcher stopped"}
        )

    def process_event(self, event: WatcherEvent) -> None:
        """Process a detected event (not used, events are processed in poll loop)."""
        pass


def run_gmail_watcher(
    vault_path: Path,
    credentials_path: Path | None = None,
    poll_interval: int = 120,
) -> None:
    """Run the Gmail watcher continuously.

    Args:
        vault_path: Path to the Obsidian vault
        credentials_path: Path to Gmail OAuth2 credentials
        poll_interval: Polling interval in seconds
    """
    config = VaultConfig(root=vault_path)
    watcher = GmailWatcher(config, credentials_path=credentials_path)
    watcher.POLL_INTERVAL = poll_interval

    print(f"Starting Gmail watcher for vault: {vault_path}")
    print(f"Poll interval: {poll_interval} seconds")
    watcher.start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopping Gmail watcher...")
        watcher.stop()
        print("Gmail watcher stopped.")
