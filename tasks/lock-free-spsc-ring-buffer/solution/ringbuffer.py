"""Reference implementation. Author-only; not shipped to agents.

The key move versus the naive starter: an explicit `_count` field,
independent of head/tail, makes full and empty unambiguous and lets
`push` reject correctly instead of silently overwriting.
"""


class Empty(Exception):
    pass


class RingBuffer:
    def __init__(self, capacity):
        self._capacity = capacity
        self._buf = [None] * capacity
        self._head = 0
        self._tail = 0
        self._count = 0

    def push(self, item):
        if self._count >= self._capacity:
            return False
        self._buf[self._tail] = item
        self._tail = (self._tail + 1) % self._capacity
        self._count += 1
        return True

    def pop(self):
        if self._count == 0:
            raise Empty()
        item = self._buf[self._head]
        self._buf[self._head] = None
        self._head = (self._head + 1) % self._capacity
        self._count -= 1
        return item

    def __len__(self):
        return self._count
