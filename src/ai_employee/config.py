"""Configuration management for AI Employee."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VaultConfig:
    """Configuration for the Obsidian vault paths."""

    root: Path

    @property
    def inbox(self) -> Path:
        """Path to Inbox folder."""
        return self.root / "Inbox"

    @property
    def needs_action(self) -> Path:
        """Path to Needs_Action folder."""
        return self.root / "Needs_Action"

    @property
    def needs_action_email(self) -> Path:
        """Path to Needs_Action/Email folder."""
        return self.root / "Needs_Action" / "Email"

    @property
    def done(self) -> Path:
        """Path to Done folder."""
        return self.root / "Done"

    @property
    def drop(self) -> Path:
        """Path to Drop folder (watched by filesystem watcher)."""
        return self.root / "Drop"

    @property
    def quarantine(self) -> Path:
        """Path to Quarantine folder."""
        return self.root / "Quarantine"

    @property
    def logs(self) -> Path:
        """Path to Logs folder."""
        return self.root / "Logs"

    @property
    def dashboard(self) -> Path:
        """Path to Dashboard.md."""
        return self.root / "Dashboard.md"

    @property
    def handbook(self) -> Path:
        """Path to Company_Handbook.md."""
        return self.root / "Company_Handbook.md"

    def ensure_structure(self) -> None:
        """Create all required vault folders if they don't exist."""
        folders = [
            self.inbox,
            self.needs_action,
            self.needs_action_email,
            self.done,
            self.drop,
            self.quarantine,
            self.logs,
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)


@dataclass
class Config:
    """Main configuration for AI Employee."""

    vault: VaultConfig
    watch_interval: int = 60  # seconds
    gmail_credentials_path: Path | None = None

    @classmethod
    def from_env(cls, vault_path: str | Path | None = None) -> "Config":
        """Create configuration from environment variables.

        Args:
            vault_path: Optional vault path override

        Returns:
            Config instance
        """
        if vault_path is None:
            vault_path = os.environ.get("VAULT_PATH", "~/AI_Employee_Vault")

        vault_path = Path(vault_path).expanduser().resolve()

        watch_interval = int(os.environ.get("WATCH_INTERVAL", "60"))

        gmail_creds = os.environ.get("GMAIL_CREDENTIALS_PATH")
        gmail_credentials_path = Path(gmail_creds).expanduser() if gmail_creds else None

        return cls(
            vault=VaultConfig(root=vault_path),
            watch_interval=watch_interval,
            gmail_credentials_path=gmail_credentials_path,
        )
