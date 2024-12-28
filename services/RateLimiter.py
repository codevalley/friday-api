"""Rate limiter for API calls."""

import time
from datetime import datetime, timedelta, UTC
from typing import List, Tuple


class RateLimiter:
    """Rate limiter for API calls with token tracking."""

    def __init__(
        self,
        requests_per_minute: int,
        tokens_per_minute: int,
        max_wait_seconds: int = 60,
    ):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            tokens_per_minute: Maximum tokens per minute
            max_wait_seconds: Maximum seconds to wait for capacity
        """
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.max_wait_seconds = max_wait_seconds
        self.request_history: List[datetime] = []
        self.token_history: List[Tuple[datetime, int]] = []

    def _clean_history(self, now: datetime) -> None:
        """Clean up history older than 1 minute.

        Args:
            now: Current timestamp
        """
        one_minute_ago = now - timedelta(minutes=1)
        self.request_history = [
            ts
            for ts in self.request_history
            if ts > one_minute_ago
        ]
        self.token_history = [
            (ts, tokens)
            for ts, tokens in self.token_history
            if ts > one_minute_ago
        ]

    def _get_current_usage(
        self, now: datetime
    ) -> Tuple[int, int]:
        """Get current request and token counts.

        Args:
            now: Current timestamp

        Returns:
            Tuple of (request_count, token_count)
        """
        self._clean_history(now)
        request_count = len(self.request_history)
        token_count = sum(
            tokens for _, tokens in self.token_history
        )
        return request_count, token_count

    def _has_capacity(
        self, now: datetime, tokens: int
    ) -> bool:
        """Check if there is capacity for a request.

        Args:
            now: Current timestamp
            tokens: Number of tokens needed

        Returns:
            Whether there is capacity
        """
        (
            request_count,
            token_count,
        ) = self._get_current_usage(now)
        return (
            request_count < self.requests_per_minute
            and token_count + tokens
            <= self.tokens_per_minute
        )

    def wait_for_capacity(self, tokens: int) -> bool:
        """Wait for rate limit capacity.

        Args:
            tokens: Number of tokens needed

        Returns:
            Whether capacity was acquired
        """
        start_time = time.time()
        while (
            time.time() - start_time < self.max_wait_seconds
        ):
            now = datetime.now(UTC)
            if self._has_capacity(now, tokens):
                self.request_history.append(now)
                return True
            time.sleep(1)
        return False

    def record_usage(
        self, timestamp: datetime, tokens: int
    ) -> None:
        """Record token usage.

        Args:
            timestamp: When the usage occurred
            tokens: Number of tokens used
        """
        self.token_history.append((timestamp, tokens))
        self._clean_history(datetime.now(UTC))
