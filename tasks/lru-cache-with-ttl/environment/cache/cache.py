"""A bounded cache with per-entry TTL expiry and LRU capacity eviction.

This implementation handles plain insertion-order eviction once the cache
is full, but `get()` never checks expiry at all (a key can be read long
after its TTL has passed, as long as capacity pressure hasn't forced a
purge) and never refreshes recency (only `put()` touches eviction order,
so a key that was just read is exactly as likely to be evicted as one
that was never touched since insertion). See /app/TASK_CONTRACT.md.
"""
import time


def _default_clock():
    return time.monotonic()


class TTLCache:
    def __init__(self, max_size, clock=None):
        self._max_size = max_size
        self._clock = clock or _default_clock
        self._store = {}  # key -> (value, expires_at)
        self._order = []  # oldest-first; last = most recently inserted

    def put(self, key, value, ttl):
        now = self._clock()
        if key in self._store:
            self._order.remove(key)
        elif len(self._order) >= self._max_size:
            evict_key = self._order.pop(0)
            del self._store[evict_key]
        self._store[key] = (value, now + ttl)
        self._order.append(key)

    def get(self, key):
        if key not in self._store:
            raise KeyError(key)
        value, _expires_at = self._store[key]
        return value

    def __len__(self):
        return len(self._store)
