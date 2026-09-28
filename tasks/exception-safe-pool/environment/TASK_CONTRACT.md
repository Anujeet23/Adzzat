# Exception-safe resource pool — contract

Source: an original, minimal starter at `/app/repo/pool`, not a fork of an existing project.

## API

```python
class PoolExhausted(Exception): ...

class ResourcePool:
    def __init__(self, factory, max_size, destroy=None): ...
    def acquire(self) -> "ResourceHandle": ...
    def release(self, handle) -> None: ...
    @property
    def available(self) -> int: ...
    @property
    def outstanding(self) -> int: ...
    @property
    def created_total(self) -> int: ...
    @property
    def destroyed_total(self) -> int: ...

class ResourceHandle:
    resource  # whatever factory() returned
    def mark_broken(self) -> None: ...
    def __enter__(self) -> "ResourceHandle": ...
    def __exit__(self, exc_type, exc, tb) -> bool: ...  # must not suppress the exception
```

`factory` is a zero-argument callable that constructs a new resource; it may raise. `destroy`, if given, is a one-argument callable invoked exactly once for each resource that is discarded rather than returned to the pool. There is no `blocking` parameter and no blocking behavior: `acquire()` on an exhausted pool raises `PoolExhausted` immediately. Nothing about waiting for another thread to release is specified or graded.

## Guarantees

1. **No lost capacity on factory failure.** If `factory()` raises during `acquire()`, that exception propagates to the caller, but the pool's capacity is unaffected: `outstanding` must not have increased, and a subsequent `acquire()` must be able to succeed (up to `max_size` concurrently outstanding resources), even immediately afterward.
2. **No lost capacity on caller exceptions.** `with pool.acquire() as h: ...` must call `release(h)` when the block exits, whether or not an exception propagated out of it, and must not suppress that exception. After the block exits, capacity must be exactly as if the resource had been used and released normally -- an exception in the caller's own code, by itself, is not evidence that the resource is broken.
3. **`mark_broken()` means discard, not reuse.** If `h.mark_broken()` was called before `release(h)` (directly, or via a `with` block that calls it before raising or returning), that resource must never be handed out again by a later `acquire()`, and `destroy()` must be called on it exactly once, synchronously, during that `release()` call. Capacity for a *different*, freshly constructed resource must still reach `max_size` on a later `acquire()`.
4. **No double-issue, no double-release.** Two live handles must never wrap the same underlying resource at the same time. Releasing (or exiting the `with` block for) an already-released handle is a caller error and may raise.
5. **Accounting stays consistent.** At every point, `outstanding + available == max_size`, and `outstanding` never goes negative.

## What's out of scope

Real thread-based blocking/waiting, resource health checks initiated by the pool itself, and any specific resource type (`factory` and `destroy` are provided by the caller; the pool must not assume anything about what they return beyond "an object").

## Delivery

Copy the complete `pool` package to `/app/submission/pool`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
