Make the bounded resource pool at `/app/repo/pool` exception-safe: no sequence of factory failures, caller exceptions, or explicitly broken resources may ever permanently shrink its capacity, hand out a resource that's already checked out, or leave a discarded resource's cleanup uncalled. Read `/app/TASK_CONTRACT.md` for the exact API and guarantees before changing anything; `/app/reproduce.py` demonstrates two capacity leaks in the current implementation.

## Interface

`pool.ResourcePool(factory, max_size, destroy=None)` implements `acquire() -> ResourceHandle` (raises `PoolExhausted` if none available; propagates whatever `factory()` raises if construction fails) and `release(handle)`. `pool.ResourceHandle` exposes `.resource`, `.mark_broken()`, and the context-manager protocol so `with pool.acquire() as h: ...` releases automatically on exit -- with or without an exception. There is no blocking/waiting behavior: an exhausted pool always raises immediately, and nothing about waiting for another thread is specified or graded.

## Required guarantees

1. If `factory()` raises during `acquire()`, that exception propagates, but the pool's capacity is untouched: `outstanding` must not have increased, and a following `acquire()` must be able to succeed.
2. `with pool.acquire() as h: ...` must call `release(h)` on exit regardless of whether the block raised, and must not suppress that exception. A caller exception, by itself, is not evidence the resource is broken -- capacity must be exactly as if the block had returned normally.
3. If `h.mark_broken()` was called before release, the resource must never be handed out again, and `destroy()` (when supplied) must be called on it exactly once, synchronously, inside that `release()` call. Capacity for a different, freshly constructed resource must still be able to reach `max_size` afterward.
4. Two live handles must never wrap the same underlying resource at the same time. Releasing an already-released handle is a caller error.
5. At every point, `outstanding + available == max_size`, and `outstanding` never goes negative.

## Deliverable

Copy the complete, working `pool` package to `/app/submission/pool`. The verifier imports only `/app/submission/pool` as an unprivileged user in a separate container; it does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria, all run against real exception propagation through the actual pool object, not mocked or inspected via source analysis: basic correctness with no failures injected (15%); exception safety when caller code raises while holding a resource, both with and without `mark_broken()` (30%); correct, exactly-once `destroy()` handling for explicitly broken resources (25%); resilience to a resource-factory failure that must not permanently lose a slot (20%); and a longer mixed sequence combining all of the above, checked only by final invariants (10%). A full pass requires all five; per-criterion outcomes are retained separately for diagnosis.

Only the Python standard library is available at verification time; no network access.
