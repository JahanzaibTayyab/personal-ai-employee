"""Tests for sensitive data redaction utilities."""

from ai_employee.utils.redaction import (
    REDACTED,
    is_sensitive_key,
    redact_dict,
    redact_string,
)


class TestRedactString:
    def test_redacts_api_key(self) -> None:
        text = "api_key=sk_live_1234567890abcdef"
        result = redact_string(text)
        assert "sk_live_1234567890abcdef" not in result
        assert REDACTED in result

    def test_redacts_bearer_token(self) -> None:
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = redact_string(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    def test_redacts_password(self) -> None:
        text = "password=my_secret_password123"
        result = redact_string(text)
        assert "my_secret_password123" not in result

    def test_preserves_non_sensitive_text(self) -> None:
        text = "Hello, this is a normal log message about processing invoices."
        result = redact_string(text)
        assert result == text

    def test_redacts_credit_card(self) -> None:
        text = "Card: 4111-1111-1111-1111"
        result = redact_string(text)
        assert "4111-1111-1111-1111" not in result

    def test_redacts_ssn(self) -> None:
        text = "SSN: 123-45-6789"
        result = redact_string(text)
        assert "123-45-6789" not in result


class TestRedactDict:
    def test_redacts_sensitive_keys(self) -> None:
        data = {
            "username": "admin",
            "password": "secret123",
            "api_key": "sk_live_abcdef",
        }
        result = redact_dict(data)
        assert result["username"] == "admin"
        assert result["password"] == REDACTED
        assert result["api_key"] == REDACTED

    def test_redacts_nested_dicts(self) -> None:
        data = {
            "config": {
                "url": "https://example.com",
                "token": "secret_token_value",
            }
        }
        result = redact_dict(data)
        assert result["config"]["url"] == "https://example.com"  # type: ignore[index]
        assert result["config"]["token"] == REDACTED  # type: ignore[index]

    def test_redacts_list_values(self) -> None:
        data = {
            "credentials": [
                {"name": "odoo", "secret": "abc123"},
                {"name": "meta", "secret": "def456"},
            ]
        }
        result = redact_dict(data)
        assert result["credentials"] == REDACTED

    def test_preserves_non_sensitive_data(self) -> None:
        data = {
            "name": "John",
            "age": 30,
            "active": True,
        }
        result = redact_dict(data)
        assert result == data

    def test_handles_max_depth(self) -> None:
        deep: dict[str, object] = {"level": {"level": {"level": {"password": "secret"}}}}
        result = redact_dict(deep, max_depth=2)
        assert isinstance(result["level"], dict)

    def test_handles_empty_dict(self) -> None:
        assert redact_dict({}) == {}


class TestIsSensitiveKey:
    def test_password_is_sensitive(self) -> None:
        assert is_sensitive_key("password") is True

    def test_api_key_is_sensitive(self) -> None:
        assert is_sensitive_key("api_key") is True
        assert is_sensitive_key("API_KEY") is True

    def test_name_is_not_sensitive(self) -> None:
        assert is_sensitive_key("name") is False

    def test_hyphenated_keys(self) -> None:
        assert is_sensitive_key("api-key") is True
        assert is_sensitive_key("access-token") is True
