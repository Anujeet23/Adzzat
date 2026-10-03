"""Reference implementation. Author-only; not shipped to agents.

The key move versus the naive starter: expiry is checked on every `get()`
against the live clock (not just enforced lazily at insertion time), a
successful `get()` moves the key to the most-recently-used end of the
eviction order, and `put()` purges all already-expired entries before
ever considering an LRU eviction of a live one.
"""
import time


def _default_clock():
    return time.monotonic()


class TTLCache:
    def __init__(self, max_size, clock=None):
        self._max_size = max_size
        self._clock = clock or _default_clock
        self._store = {}  # key -> (value, expires_at)
        self._order = []  # oldest-first; last = most recently used

    def _purge_expired(self, now):
        expired = [key for key, (_, expires_at) in self._store.items() if expires_at <= now]
        for key in expired:
            del self._store[key]
            self._order.remove(key)

    def put(self, key, value, ttl):
        now = self._clock()
        self._purge_expired(now)
        if key in self._store:
            self._order.remove(key)
        elif len(self._store) >= self._max_size:
            evict_key = self._order.pop(0)
            del self._store[evict_key]
        self._store[key] = (value, now + ttl)
        self._order.append(key)

    def get(self, key):
        now = self._clock()
        if key not in self._store:
            raise KeyError(key)
        value, expires_at = self._store[key]
        if expires_at <= now:
            del self._store[key]
            self._order.remove(key)
            raise KeyError(key)
        self._order.remove(key)
        self._order.append(key)
        return value

    def __len__(self):
        now = self._clock()
        return sum(1 for _, expires_at in self._store.values() if expires_at > now)
