"""Tests for frontmatter utility."""

from ai_employee.utils.frontmatter import generate_frontmatter, parse_frontmatter


class TestGenerateFrontmatter:
    """Tests for generating YAML frontmatter."""

    def test_generate_simple_frontmatter(self) -> None:
        """Test generating frontmatter with simple values."""
        data = {"title": "Test", "status": "pending"}
        content = "Body content"

        result = generate_frontmatter(data, content)

        assert result.startswith("---\n")
        assert "title: Test" in result
        assert "status: pending" in result
        assert result.endswith("Body content")

    def test_generate_frontmatter_with_empty_content(self) -> None:
        """Test generating frontmatter with empty body."""
        data = {"type": "file_drop"}
        content = ""

        result = generate_frontmatter(data, content)

        assert "type: file_drop" in result
        assert result.strip().endswith("---")

    def test_generate_frontmatter_preserves_content(self) -> None:
        """Test that body content is preserved."""
        data = {"key": "value"}
        content = "## Header\n\nParagraph text."

        result = generate_frontmatter(data, content)

        assert "## Header" in result
        assert "Paragraph text." in result


class TestParseFrontmatter:
    """Tests for parsing YAML frontmatter."""

    def test_parse_frontmatter_extracts_data(self) -> None:
        """Test parsing frontmatter from markdown."""
        markdown = """---
title: Test Document
status: pending
priority: high
---

## Content

Body text here.
"""
        data, content = parse_frontmatter(markdown)

        assert data["title"] == "Test Document"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert "## Content" in content
        assert "Body text here." in content

    def test_parse_frontmatter_with_no_frontmatter(self) -> None:
        """Test parsing markdown without frontmatter."""
        markdown = "# Just a heading\n\nSome content."

        data, content = parse_frontmatter(markdown)

        assert data == {}
        assert "# Just a heading" in content

    def test_parse_frontmatter_handles_empty_string(self) -> None:
        """Test parsing empty string."""
        data, content = parse_frontmatter("")

        assert data == {}
        assert content == ""
