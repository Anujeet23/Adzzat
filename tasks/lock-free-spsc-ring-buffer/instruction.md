Fix the fixed-capacity ring buffer at `/app/repo/ringbuffer` so it correctly distinguishes "full" from "empty": the current implementation tracks only head/tail indices with no count, so `push` never actually checks capacity and silently overwrites unread data once the buffer wraps around. Read `/app/TASK_CONTRACT.md` for the exact API and guarantees before changing anything; `/app/reproduce.py` demonstrates the data corruption live.

## Interface

`ringbuffer.RingBuffer(capacity)` implements `push(item) -> bool` (returns `False` and leaves the buffer unchanged if full, otherwise stores `item` and returns `True`), `pop()` (raises `ringbuffer.Empty` if empty, otherwise removes and returns the oldest unread item), and `__len__()` (the exact number of currently held, unread items). This models a single-producer/single-consumer queue, but grading never uses real threads or timing -- every scenario is a scripted, single-threaded sequence of `push`/`pop` calls in a precise, pre-determined order, which is what a correct SPSC implementation must handle regardless of which thread actually calls what.

## Required guarantees

1. `push` on a full buffer (`len(buffer) == capacity`) must return `False` and must not alter the buffer's contents at all -- the oldest unread item must never be silently overwritten.
2. `pop` on an empty buffer must raise `ringbuffer.Empty`, never return a stale or garbage value.
3. Items come out in exactly the order they were pushed (FIFO), with no duplication and no drops, across any sequence of interleaved pushes and pops.
4. `len(buffer)` always reports the exact count of currently held, unread items, from `0` up to `capacity`.
5. Correctness holds after the underlying storage has wrapped around many times -- a long sequence whose total push count far exceeds `capacity` must behave identically to a short one, item for item.

## What's out of scope

Real multi-threaded concurrency, memory-ordering/visibility semantics, and any capacity resizing after construction -- this is single-threaded, scripted-sequence correctness only.

## Deliverable

Copy the complete `ringbuffer` package to `/app/submission/ringbuffer`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria, each a scripted sequence of `push`/`pop`/`len` checks against the actual submitted `RingBuffer` object:

1. **Basic correctness.** Push and pop below capacity, no wraparound. (15%)
2. **Full-buffer rejection.** A push on a full buffer must fail without corrupting existing data. (25%)
3. **Empty-buffer rejection.** A pop on an empty buffer must raise, never fabricate a value. (15%)
4. **Wraparound integrity.** Many push/pop cycles whose total count far exceeds capacity, checked for exact FIFO order throughout. (25%)
5. **A longer mixed sequence** combining all of the above, checked at every step. (20%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only the Python standard library is available at verification time; no network access.
