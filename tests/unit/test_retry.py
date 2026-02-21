"""Tests for exponential backoff retry utilities."""

from unittest.mock import patch

import pytest

from ai_employee.models.enums import ErrorCategory
from ai_employee.utils.retry import (
    RetryExhaustedError,
    calculate_backoff,
    classify_error,
    is_retryable,
    with_retry,
)


class TestClassifyError:
    def test_timeout_is_transient(self) -> None:
        error = TimeoutError("Connection timed out")
        assert classify_error(error) == ErrorCategory.TRANSIENT

    def test_connection_error_is_transient(self) -> None:
        error = ConnectionError("Network unreachable")
        assert classify_error(error) == ErrorCategory.TRANSIENT

    def test_rate_limit_is_transient(self) -> None:
        error = Exception("Rate limit exceeded (429)")
        assert classify_error(error) == ErrorCategory.TRANSIENT

    def test_auth_error_is_authentication(self) -> None:
        error = PermissionError("Authentication failed")
        assert classify_error(error) == ErrorCategory.AUTHENTICATION

    def test_forbidden_is_authentication(self) -> None:
        error = Exception("403 Forbidden")
        assert classify_error(error) == ErrorCategory.AUTHENTICATION

    def test_validation_is_data(self) -> None:
        error = ValueError("Validation error: invalid email")
        assert classify_error(error) == ErrorCategory.DATA

    def test_os_error_is_system(self) -> None:
        error = OSError("Disk full")
        assert classify_error(error) == ErrorCategory.SYSTEM

    def test_generic_error_is_logic(self) -> None:
        error = RuntimeError("Something went wrong")
        assert classify_error(error) == ErrorCategory.LOGIC


class TestIsRetryable:
    def test_transient_is_retryable(self) -> None:
        assert is_retryable(TimeoutError("timed out")) is True

    def test_auth_is_not_retryable(self) -> None:
        assert is_retryable(PermissionError("auth failed")) is False

    def test_logic_is_not_retryable(self) -> None:
        assert is_retryable(RuntimeError("bad logic")) is False


class TestCalculateBackoff:
    def test_first_attempt(self) -> None:
        assert calculate_backoff(0, base_delay=1.0) == 1.0

    def test_second_attempt(self) -> None:
        assert calculate_backoff(1, base_delay=1.0) == 2.0

    def test_third_attempt(self) -> None:
        assert calculate_backoff(2, base_delay=1.0) == 4.0

    def test_respects_max_delay(self) -> None:
        assert calculate_backoff(10, base_delay=1.0, max_delay=60.0) == 60.0

    def test_custom_base_delay(self) -> None:
        assert calculate_backoff(0, base_delay=2.0) == 2.0
        assert calculate_backoff(1, base_delay=2.0) == 4.0


class TestWithRetry:
    @patch("ai_employee.utils.retry.time.sleep")
    def test_succeeds_on_first_try(self, mock_sleep: object) -> None:
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        def succeed() -> str:
            nonlocal call_count
            call_count += 1
            return "ok"

        assert succeed() == "ok"
        assert call_count == 1

    @patch("ai_employee.utils.retry.time.sleep")
    def test_retries_transient_error(self, mock_sleep: object) -> None:
        attempt = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        def flaky() -> str:
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise TimeoutError("connection timeout")
            return "ok"

        assert flaky() == "ok"
        assert attempt == 3

    @patch("ai_employee.utils.retry.time.sleep")
    def test_does_not_retry_non_transient(self, mock_sleep: object) -> None:
        @with_retry(max_attempts=3, base_delay=0.01)
        def auth_fail() -> str:
            raise PermissionError("Authentication failed")

        with pytest.raises(PermissionError):
            auth_fail()

    @patch("ai_employee.utils.retry.time.sleep")
    def test_raises_exhausted_after_max_attempts(self, mock_sleep: object) -> None:
        @with_retry(max_attempts=2, base_delay=0.01)
        def always_timeout() -> str:
            raise TimeoutError("always times out")

        with pytest.raises(RetryExhaustedError) as exc_info:
            always_timeout()

        assert exc_info.value.attempts == 2

    @patch("ai_employee.utils.retry.time.sleep")
    def test_custom_retryable_check(self, mock_sleep: object) -> None:
        attempt = 0

        @with_retry(
            max_attempts=3,
            base_delay=0.01,
            retryable_check=lambda e: isinstance(e, ValueError),
        )
        def custom_retry() -> str:
            nonlocal attempt
            attempt += 1
            if attempt < 2:
                raise ValueError("retry this")
            return "ok"

        assert custom_retry() == "ok"
        assert attempt == 2
