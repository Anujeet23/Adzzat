"""A token-bucket rate limiter.

This implementation's refill math has two problems: it truncates the
elapsed time to whole clock units before crediting tokens, silently
dropping any fractional remainder on every call instead of carrying it
forward -- and it never clamps the balance to `capacity`, so a long idle
period lets the bucket accumulate far more tokens than it should ever
hold. See /app/TASK_CONTRACT.md.
"""
import time


def _default_clock():
    return time.monotonic()


class TokenBucket:
    def __init__(self, capacity, refill_rate, clock=None):
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._clock = clock or _default_clock
        self._tokens = float(capacity)
        self._last_refill = self._clock()

    def _refill(self):
        now = self._clock()
        elapsed = int(now - self._last_refill)
        if elapsed > 0:
            self._tokens += elapsed * self._refill_rate
            self._last_refill = self._clock()

    def try_acquire(self, cost=1):
        self._refill()
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False

    def available(self):
        self._refill()
        return self._tokens
