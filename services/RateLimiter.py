import asyncio
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls with token tracking."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 90_000,
    ):
        """Initialize the rate limiter."""
        self._requests_per_minute = requests_per_minute
        self._tokens_per_minute = tokens_per_minute
        self._request_timestamps: list[datetime] = []
        self._token_usage: dict[datetime, int] = {}
        self._lock = asyncio.Lock()

    async def acquire(
        self, estimated_tokens: Optional[int] = None
    ) -> bool:
        """Acquire permission to make an API call."""
        async with self._lock:
            now = datetime.now(UTC)
            minute_ago = now - timedelta(minutes=1)

            # Clean up old data
            self._request_timestamps = [
                ts
                for ts in self._request_timestamps
                if ts > minute_ago
            ]
            self._token_usage = {
                ts: tokens
                for ts, tokens in self._token_usage.items()
                if ts > minute_ago
            }

            # Check request rate limit
            if (
                len(self._request_timestamps)
                >= self._requests_per_minute
            ):
                return False

            # Check token rate limit if tokens are provided
            if estimated_tokens is not None:
                current_usage = self.get_current_usage()
                if (
                    current_usage + estimated_tokens
                    > self._tokens_per_minute
                ):
                    return False

            # Record request timestamp
            self._request_timestamps.append(now)
            return True

    async def record_usage(
        self, timestamp: datetime, tokens: int
    ) -> None:
        """Record token usage for a request."""
        async with self._lock:
            # If there's already a record for this timestamp, add to it
            if timestamp in self._token_usage:
                self._token_usage[timestamp] += tokens
            else:
                self._token_usage[timestamp] = tokens

    def get_current_usage(self) -> int:
        """Get the current token usage within the last minute."""
        now = datetime.now(UTC)
        minute_ago = now - timedelta(minutes=1)

        # Calculate sum of recent tokens
        recent_tokens = sum(
            tokens
            for ts, tokens in self._token_usage.items()
            if ts > minute_ago
        )
        return recent_tokens

    async def wait_for_capacity(
        self, estimated_tokens: int
    ) -> bool:
        """Wait for rate limit capacity."""
        # First check if we're over the per-minute limit
        if estimated_tokens > self._tokens_per_minute:
            return False

        retries = 3
        delay = 1.0
        attempts = 0

        while attempts < retries:
            async with self._lock:
                # Simulate time passing for each retry attempt
                now = datetime.now(UTC) + timedelta(
                    seconds=attempts * delay
                )
                minute_ago = now - timedelta(minutes=1)

                # Clean up old records
                self._token_usage = {
                    ts: tokens
                    for ts, tokens in self._token_usage.items()
                    if ts > minute_ago
                }
                self._request_timestamps = [
                    ts
                    for ts in self._request_timestamps
                    if ts > minute_ago
                ]

                # Calculate current usage after cleanup
                current_usage = sum(
                    tokens
                    for ts, tokens in self._token_usage.items()
                    if ts > minute_ago
                )

                # Check if we have capacity
                if (
                    current_usage + estimated_tokens
                    <= self._tokens_per_minute
                ):
                    # Record the usage
                    if now in self._token_usage:
                        self._token_usage[
                            now
                        ] += estimated_tokens
                    else:
                        self._token_usage[
                            now
                        ] = estimated_tokens
                    self._request_timestamps.append(now)
                    return True

            # If we don't have capacity, wait before retrying
            attempts += 1
            if attempts < retries:
                await asyncio.sleep(delay * (2**attempts))

        return False
