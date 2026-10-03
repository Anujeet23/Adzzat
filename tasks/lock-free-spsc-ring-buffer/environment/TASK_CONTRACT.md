# SPSC ring buffer — contract

Source: an original, minimal starter at `/app/repo/ringbuffer`, not a fork of an existing project.

## API

```python
class Empty(Exception): ...

class RingBuffer:
    def __init__(self, capacity: int): ...
    def push(self, item) -> bool: ...   # False if full, item unchanged
    def pop(self): ...                   # raises Empty if empty
    def __len__(self) -> int: ...
```

Grading is a single-threaded, scripted sequence of calls in a precise order -- no real threads, no timing. A correct implementation must handle any such sequence identically to how it would handle calls arriving from separate producer/consumer threads in that same order.

## Guarantees

1. **Full means full.** `push` on a buffer already holding `capacity` items returns `False` and leaves every existing item untouched -- it must never silently overwrite the oldest unread item.
2. **Empty means empty.** `pop` on a buffer holding zero items raises `Empty`; it never returns a stale or fabricated value.
3. **Strict FIFO.** Items pop out in exactly the order they were pushed, with no duplication and no drops, under any sequence of interleaved pushes and pops.
4. **Exact length.** `len(buffer)` always equals the count of items currently held and not yet popped, between `0` and `capacity` inclusive.
5. **Wraparound is not special.** Correctness holds identically after the underlying storage index has wrapped past the end many times over a long sequence.

## What's out of scope

Real multi-threaded concurrency and memory-ordering semantics, and capacity resizing after construction.

## Delivery

Copy the complete `ringbuffer` package to `/app/submission/ringbuffer`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
