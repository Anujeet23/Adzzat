"""A bounded pool of expensive resources.

This implementation handles the happy path but is not exception-safe: a
failure in the resource factory permanently shrinks the pool's capacity,
and an exception raised by caller code while holding a resource leaks that
resource forever instead of returning it. See /app/TASK_CONTRACT.md.
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
        if exc_type is None:
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
        self._outstanding += 1
        resource = self._factory()
        self._created_total += 1
        return ResourceHandle(self, resource)

    def release(self, handle):
        self._outstanding -= 1
        if not handle._broken:
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
