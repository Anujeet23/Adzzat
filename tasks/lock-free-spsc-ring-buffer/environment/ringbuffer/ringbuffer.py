"""A fixed-capacity ring buffer.

This implementation tracks only head/tail indices with no separate
count, so `push` never actually checks whether the buffer is full before
writing -- once `tail` wraps around and catches up to `head`, it
silently overwrites unread data. `__len__`'s `(tail - head) % capacity`
formula is also ambiguous: a completely full buffer and a completely
empty one both report 0. See /app/TASK_CONTRACT.md.
"""


class Empty(Exception):
    pass


class RingBuffer:
    def __init__(self, capacity):
        self._capacity = capacity
        self._buf = [None] * capacity
        self._head = 0
        self._tail = 0

    def push(self, item):
        self._buf[self._tail] = item
        self._tail = (self._tail + 1) % self._capacity
        return True

    def pop(self):
        if self._head == self._tail:
            raise Empty()
        item = self._buf[self._head]
        self._head = (self._head + 1) % self._capacity
        return item

    def __len__(self):
        return (self._tail - self._head) % self._capacity
