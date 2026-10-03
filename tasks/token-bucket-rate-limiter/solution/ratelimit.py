"""Reference implementation. Author-only; not shipped to agents.

The key move versus the naive starter: refill uses the exact (float)
elapsed time, not a truncated integer count, and the baseline advances
to `now` only when it actually credits `now - last_refill` worth of
tokens -- so no fractional remainder is ever dropped. The balance is
clamped to `capacity` on every refill.
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
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
            self._last_refill = now

    def try_acquire(self, cost=1):
        self._refill()
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False

    def available(self):
        self._refill()
        return self._tokens
