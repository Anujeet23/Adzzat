# Token-bucket rate limiter — contract

Source: an original, minimal starter at `/app/repo/ratelimit`, not a fork of an existing project.

## API

```python
class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float, clock=None): ...
    def try_acquire(self, cost: float = 1) -> bool: ...
    def available(self) -> float: ...
```

`clock` is a zero-argument callable returning the current time as a number (defaults to `time.monotonic`); the verifier always supplies its own fake, caller-controlled clock, so real elapsed time is never part of grading. `refill_rate` is tokens granted per clock unit, continuously.

## Guarantees

1. **Capacity clamp.** The token count never exceeds `capacity`, regardless of how long the bucket sits idle before the next call.
2. **Continuous, lossless refill.** Refill amount is exactly `elapsed * refill_rate`, where `elapsed` is the exact (not truncated) time since the last refill. Many small successive advances must credit the same total as one large advance covering the same span -- no fractional remainder may be dropped at any individual refill.
3. **Exact, all-or-nothing accounting.** `try_acquire(cost)` succeeds and deducts exactly `cost` if and only if the refilled balance is `>= cost`. On failure, the balance is exactly what refilling produced -- never partially deducted, never negative.
4. **Zero elapsed time means zero refill.** Two calls at the same clock instant refill by exactly zero tokens.
5. **Read-only queries stay read-only.** `available()` reports the balance a subsequent `try_acquire()` at that same instant would see, without itself granting or consuming tokens beyond what elapsed time entitles.

## What's out of scope

Negative `refill_rate` or `capacity`, multi-threaded access, and persistence across process restarts.

## Delivery

Copy the complete `ratelimit` package to `/app/submission/ratelimit`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
