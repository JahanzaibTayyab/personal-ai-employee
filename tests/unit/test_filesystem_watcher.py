"""Tests for filesystem watcher."""

import time
from pathlib import Path

import pytest

from ai_employee.config import VaultConfig
from ai_employee.watchers.filesystem import FileSystemWatcher


@pytest.fixture
def vault_config(tmp_path: Path) -> VaultConfig:
    """Create a vault config for testing."""
    config = VaultConfig(root=tmp_path)
    config.ensure_structure()
    return config


class TestFileSystemWatcher:
    """Tests for FileSystemWatcher class."""

    def test_watcher_initializes_with_config(self, vault_config: VaultConfig) -> None:
        """Test watcher can be initialized."""
        watcher = FileSystemWatcher(vault_config)
        assert watcher.vault_config == vault_config
        assert watcher.running is False

    def test_watcher_starts_and_stops(self, vault_config: VaultConfig) -> None:
        """Test watcher can start and stop."""
        watcher = FileSystemWatcher(vault_config)

        watcher.start()
        assert watcher.running is True

        watcher.stop()
        assert watcher.running is False

    def test_watcher_is_idempotent_on_start(self, vault_config: VaultConfig) -> None:
        """Test starting watcher multiple times is safe."""
        watcher = FileSystemWatcher(vault_config)

        watcher.start()
        watcher.start()  # Should not raise
        assert watcher.running is True

        watcher.stop()

    def test_watcher_is_idempotent_on_stop(self, vault_config: VaultConfig) -> None:
        """Test stopping watcher multiple times is safe."""
        watcher = FileSystemWatcher(vault_config)

        watcher.start()
        watcher.stop()
        watcher.stop()  # Should not raise
        assert watcher.running is False

    def test_watcher_processes_dropped_file(self, vault_config: VaultConfig) -> None:
        """Test that watcher creates action item for dropped file."""
        watcher = FileSystemWatcher(vault_config)
        watcher.start()

        try:
            # Create test file
            test_file = vault_config.drop / "test_document.txt"
            test_file.write_text("Test content for watcher")

            # Wait for processing
            time.sleep(1.5)

            # Check action item was created
            action_files = list(vault_config.needs_action.glob("FILE_*.md"))
            assert len(action_files) == 1

            # Verify content
            content = action_files[0].read_text()
            assert "type: file_drop" in content
            assert "original_name: test_document.txt" in content
            assert "Test content for watcher" in content

            # Verify original was removed
            assert not test_file.exists()

        finally:
            watcher.stop()

    def test_watcher_quarantines_unsupported_files(
        self, vault_config: VaultConfig
    ) -> None:
        """Test that unsupported files are quarantined."""
        watcher = FileSystemWatcher(vault_config)
        watcher.start()

        try:
            # Create unsupported file type
            test_file = vault_config.drop / "script.exe"
            test_file.write_text("fake executable")

            # Wait for processing
            time.sleep(1.5)

            # Check file was quarantined
            quarantined = list(vault_config.quarantine.glob("script.exe*"))
            assert len(quarantined) >= 1

        finally:
            watcher.stop()

    def test_supported_extensions(self, vault_config: VaultConfig) -> None:
        """Test that supported extensions are defined."""
        watcher = FileSystemWatcher(vault_config)

        assert ".txt" in watcher.SUPPORTED_EXTENSIONS
        assert ".pdf" in watcher.SUPPORTED_EXTENSIONS
        assert ".md" in watcher.SUPPORTED_EXTENSIONS
        assert ".json" in watcher.SUPPORTED_EXTENSIONS
        assert ".csv" in watcher.SUPPORTED_EXTENSIONS
