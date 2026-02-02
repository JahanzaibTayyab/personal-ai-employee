"""Tests for handbook service."""

import pytest

from ai_employee.services.handbook import detect_priority_from_text


class TestDetectPriority:
    """Tests for priority detection from text."""

    def test_detect_urgent_priority(self) -> None:
        """Test detection of urgent priority keywords."""
        from ai_employee.models.action_item import Priority

        assert detect_priority_from_text("This is URGENT please respond") == Priority.URGENT
        assert detect_priority_from_text("Need this ASAP") == Priority.URGENT
        assert detect_priority_from_text("EMERGENCY meeting") == Priority.URGENT

    def test_detect_high_priority(self) -> None:
        """Test detection of high priority keywords."""
        from ai_employee.models.action_item import Priority

        assert detect_priority_from_text("Important document attached") == Priority.HIGH
        assert detect_priority_from_text("High priority task") == Priority.HIGH

    def test_detect_normal_priority_when_no_keywords(self) -> None:
        """Test that normal priority is returned when no keywords found."""
        from ai_employee.models.action_item import Priority

        assert detect_priority_from_text("Regular meeting notes") == Priority.NORMAL
        assert detect_priority_from_text("Weekly report") == Priority.NORMAL
        assert detect_priority_from_text("") == Priority.NORMAL

    def test_case_insensitive_detection(self) -> None:
        """Test that detection is case insensitive."""
        from ai_employee.models.action_item import Priority

        assert detect_priority_from_text("urgent") == Priority.URGENT
        assert detect_priority_from_text("URGENT") == Priority.URGENT
        assert detect_priority_from_text("Urgent") == Priority.URGENT
        assert detect_priority_from_text("important") == Priority.HIGH
        assert detect_priority_from_text("IMPORTANT") == Priority.HIGH

    def test_urgent_takes_precedence_over_high(self) -> None:
        """Test that urgent priority takes precedence over high."""
        from ai_employee.models.action_item import Priority

        text = "This is both important and urgent"
        assert detect_priority_from_text(text) == Priority.URGENT
