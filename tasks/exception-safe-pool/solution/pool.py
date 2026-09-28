"""Reference exception-safe implementation. Author-only; not shipped to agents.

The key move versus the naive starter: `_outstanding` is only incremented
*after* `factory()` has returned successfully, so a factory failure never
needs to be unwound. `ResourceHandle.__exit__` always calls `release()`,
unconditionally, so a caller exception can never leak a resource.
"""


class PoolExhausted(Exception):
    pass


class ResourceHandle:
    def __init__(self, pool, resource):
        self._pool = pool
        self.resource = resource
        self._broken = False
        self._released = False

    def mark_broken(self):
        self._broken = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._pool.release(self)
        return False


class ResourcePool:
    def __init__(self, factory, max_size, destroy=None):
        self._factory = factory
        self._max_size = max_size
        self._destroy = destroy or (lambda resource: None)
        self._free = []
        self._outstanding = 0
        self._created_total = 0
        self._destroyed_total = 0

    def acquire(self):
        if self._free:
            resource = self._free.pop()
            self._outstanding += 1
            return ResourceHandle(self, resource)
        if self._outstanding + len(self._free) >= self._max_size:
            raise PoolExhausted()
        resource = self._factory()
        self._created_total += 1
        self._outstanding += 1
        return ResourceHandle(self, resource)

    def release(self, handle):
        if handle._released:
            raise ValueError("handle already released")
        handle._released = True
        self._outstanding -= 1
        if handle._broken:
            self._destroy(handle.resource)
            self._destroyed_total += 1
        else:
            self._free.append(handle.resource)

    @property
    def available(self):
        return self._max_size - self._outstanding

    @property
    def outstanding(self):
        return self._outstanding

    @property
    def created_total(self):
        return self._created_total

    @property
    def destroyed_total(self):
        return self._destroyed_total
