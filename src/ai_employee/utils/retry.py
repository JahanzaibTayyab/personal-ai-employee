"""Exponential backoff retry utilities for Gold tier error recovery."""

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from ai_employee.models.enums import ErrorCategory

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, attempts: int, last_error: Exception) -> None:
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Retry exhausted after {attempts} attempts: {last_error}"
        )


def classify_error(error: Exception) -> ErrorCategory:
    """Classify an error into a recovery category.

    Args:
        error: The exception to classify

    Returns:
        ErrorCategory indicating the type of failure
    """
    error_type = type(error).__name__.lower()
    error_msg = str(error).lower()

    auth_indicators = ("auth", "credential", "permission", "forbidden", "401", "403")
    transient_indicators = (
        "timeout", "connection", "network", "temporary", "retry",
        "503", "502", "429", "rate limit", "throttl",
    )
    data_indicators = ("validation", "invalid", "parse", "format", "schema")

    if any(ind in error_type or ind in error_msg for ind in auth_indicators):
        return ErrorCategory.AUTHENTICATION

    if any(ind in error_type or ind in error_msg for ind in transient_indicators):
        return ErrorCategory.TRANSIENT

    if any(ind in error_type or ind in error_msg for ind in data_indicators):
        return ErrorCategory.DATA

    if isinstance(error, (OSError, SystemError, MemoryError)):
        return ErrorCategory.SYSTEM

    return ErrorCategory.LOGIC


def is_retryable(error: Exception) -> bool:
    """Determine if an error is worth retrying.

    Args:
        error: The exception to check

    Returns:
        True if the error is transient and worth retrying
    """
    category = classify_error(error)
    return category == ErrorCategory.TRANSIENT


def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Delay in seconds
    """
    delay = base_delay * (2 ** attempt)
    return float(min(delay, max_delay))


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_check: Callable[[Exception], bool] | None = None,
) -> Callable[[F], F]:
    """Decorator for synchronous functions with exponential backoff retry.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        retryable_check: Optional custom function to determine if error is retryable

    Returns:
        Decorated function with retry logic
    """
    check = retryable_check or is_retryable

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt + 1 >= max_attempts or not check(e):
                        raise RetryExhaustedError(attempt + 1, e) if check(e) else e

                    delay = calculate_backoff(attempt, base_delay, max_delay)
                    logger.warning(
                        "Retry %d/%d for %s after %.1fs: %s",
                        attempt + 1,
                        max_attempts,
                        func.__name__,
                        delay,
                        e,
                    )
                    time.sleep(delay)

            raise RetryExhaustedError(max_attempts, last_error)  # type: ignore[arg-type]

        return wrapper  # type: ignore[return-value]

    return decorator


def with_async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_check: Callable[[Exception], bool] | None = None,
) -> Callable[[F], F]:
    """Decorator for async functions with exponential backoff retry.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        retryable_check: Optional custom function to determine if error is retryable

    Returns:
        Decorated async function with retry logic
    """
    check = retryable_check or is_retryable

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt + 1 >= max_attempts or not check(e):
                        raise RetryExhaustedError(attempt + 1, e) if check(e) else e

                    delay = calculate_backoff(attempt, base_delay, max_delay)
                    logger.warning(
                        "Async retry %d/%d for %s after %.1fs: %s",
                        attempt + 1,
                        max_attempts,
                        func.__name__,
                        delay,
                        e,
                    )
                    await asyncio.sleep(delay)

            raise RetryExhaustedError(max_attempts, last_error)  # type: ignore[arg-type]

        return wrapper  # type: ignore[return-value]

    return decorator
