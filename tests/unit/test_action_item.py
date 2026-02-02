"""Tests for ActionItem model."""

from datetime import datetime

import pytest

from ai_employee.models.action_item import (
    ActionItem,
    ActionItemStatus,
    ActionItemType,
    Priority,
    SourceType,
)


class TestActionItem:
    """Tests for ActionItem dataclass."""

    def test_create_file_drop_action_item(self) -> None:
        """Test creating a file drop action item."""
        item = ActionItem(
            type=ActionItemType.FILE_DROP,
            source=SourceType.FILESYSTEM,
            original_name="test.txt",
            created=datetime(2026, 1, 15, 10, 30, 0),
            status=ActionItemStatus.PENDING,
            priority=Priority.NORMAL,
            file_size=1024,
            file_type=".txt",
        )

        assert item.type == ActionItemType.FILE_DROP
        assert item.source == SourceType.FILESYSTEM
        assert item.original_name == "test.txt"
        assert item.status == ActionItemStatus.PENDING
        assert item.priority == Priority.NORMAL
        assert item.file_size == 1024
        assert item.file_type == ".txt"

    def test_create_email_action_item(self) -> None:
        """Test creating an email action item."""
        item = ActionItem(
            type=ActionItemType.EMAIL,
            source=SourceType.GMAIL,
            original_name="Important Meeting",
            created=datetime(2026, 1, 15, 10, 30, 0),
            status=ActionItemStatus.PENDING,
            priority=Priority.HIGH,
            from_address="sender@example.com",
            message_id="abc123",
        )

        assert item.type == ActionItemType.EMAIL
        assert item.source == SourceType.GMAIL
        assert item.from_address == "sender@example.com"
        assert item.message_id == "abc123"

    def test_get_filename_for_file_drop(self) -> None:
        """Test filename generation for file drop."""
        item = ActionItem(
            type=ActionItemType.FILE_DROP,
            source=SourceType.FILESYSTEM,
            original_name="document.pdf",
            created=datetime(2026, 1, 15, 10, 30, 0),
            status=ActionItemStatus.PENDING,
            priority=Priority.NORMAL,
        )

        filename = item.get_filename()
        assert filename.startswith("FILE_document.pdf")
        assert filename.endswith(".md")

    def test_get_filename_for_email(self) -> None:
        """Test filename generation for email uses message_id."""
        item = ActionItem(
            type=ActionItemType.EMAIL,
            source=SourceType.GMAIL,
            original_name="Meeting Request",
            created=datetime(2026, 1, 15, 10, 30, 0),
            status=ActionItemStatus.PENDING,
            priority=Priority.HIGH,
            message_id="msg_abc123",
        )

        filename = item.get_filename()
        assert filename == "EMAIL_msg_abc123.md"

    def test_to_frontmatter_includes_required_fields(self) -> None:
        """Test that frontmatter includes all required fields."""
        item = ActionItem(
            type=ActionItemType.FILE_DROP,
            source=SourceType.FILESYSTEM,
            original_name="test.txt",
            created=datetime(2026, 1, 15, 10, 30, 0),
            status=ActionItemStatus.PENDING,
            priority=Priority.URGENT,
            file_size=512,
            file_type=".txt",
        )

        frontmatter = item.to_frontmatter()

        assert frontmatter["type"] == "file_drop"
        assert frontmatter["source"] == "filesystem"
        assert frontmatter["original_name"] == "test.txt"
        assert frontmatter["status"] == "pending"
        assert frontmatter["priority"] == "urgent"
        assert frontmatter["file_size"] == 512
        assert frontmatter["file_type"] == ".txt"

    def test_priority_enum_values(self) -> None:
        """Test priority enum has expected values."""
        assert Priority.LOW.value == "low"
        assert Priority.NORMAL.value == "normal"
        assert Priority.HIGH.value == "high"
        assert Priority.URGENT.value == "urgent"

    def test_status_enum_values(self) -> None:
        """Test status enum has expected values."""
        assert ActionItemStatus.PENDING.value == "pending"
        assert ActionItemStatus.PROCESSING.value == "processing"
        assert ActionItemStatus.DONE.value == "done"
        assert ActionItemStatus.QUARANTINED.value == "quarantined"
