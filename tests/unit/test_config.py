"""Tests for VaultConfig."""

from pathlib import Path

import pytest

from ai_employee.config import VaultConfig


@pytest.fixture
def temp_vault(tmp_path: Path) -> VaultConfig:
    """Create a temporary vault for testing."""
    return VaultConfig(root=tmp_path)


class TestVaultConfig:
    """Tests for VaultConfig class."""

    def test_init_sets_root(self, tmp_path: Path) -> None:
        """Test that root path is set correctly."""
        config = VaultConfig(root=tmp_path)
        assert config.root == tmp_path

    def test_folder_paths_are_correct(self, temp_vault: VaultConfig) -> None:
        """Test that all folder paths are derived from root."""
        root = temp_vault.root
        assert temp_vault.inbox == root / "Inbox"
        assert temp_vault.needs_action == root / "Needs_Action"
        assert temp_vault.needs_action_email == root / "Needs_Action" / "Email"
        assert temp_vault.done == root / "Done"
        assert temp_vault.drop == root / "Drop"
        assert temp_vault.quarantine == root / "Quarantine"
        assert temp_vault.logs == root / "Logs"

    def test_file_paths_are_correct(self, temp_vault: VaultConfig) -> None:
        """Test that file paths are derived from root."""
        root = temp_vault.root
        assert temp_vault.dashboard == root / "Dashboard.md"
        assert temp_vault.handbook == root / "Company_Handbook.md"

    def test_ensure_structure_creates_folders(self, temp_vault: VaultConfig) -> None:
        """Test that ensure_structure creates all required folders."""
        temp_vault.ensure_structure()

        assert temp_vault.inbox.exists()
        assert temp_vault.inbox.is_dir()
        assert temp_vault.needs_action.exists()
        assert temp_vault.needs_action_email.exists()
        assert temp_vault.done.exists()
        assert temp_vault.drop.exists()
        assert temp_vault.quarantine.exists()
        assert temp_vault.logs.exists()

    def test_ensure_structure_is_idempotent(self, temp_vault: VaultConfig) -> None:
        """Test that ensure_structure can be called multiple times."""
        temp_vault.ensure_structure()
        temp_vault.ensure_structure()  # Should not raise

        assert temp_vault.inbox.exists()
