Fix the token-bucket rate limiter at `/app/repo/ratelimit` so its refill math is actually correct: it must never grant more tokens than its capacity, and it must never silently lose fractional refill time across repeated small calls. Read `/app/TASK_CONTRACT.md` for the exact API and guarantees before changing anything; `/app/reproduce.py` demonstrates both problems live, with a fake, caller-controlled clock so nothing about real elapsed time is involved.

## Interface

`ratelimit.TokenBucket(capacity, refill_rate, clock=None)` implements `try_acquire(cost=1) -> bool` (deducts `cost` tokens and returns `True` if available, otherwise returns `False` and leaves the balance untouched) and `available() -> float` (the current token count, without consuming any). `refill_rate` is tokens granted per clock unit, continuously, not in discrete per-call increments. `clock` is a zero-argument callable returning the current time as a number; the verifier always supplies its own fake, caller-controlled one, so nothing about real elapsed time is ever graded.

## Required guarantees

1. The token count must never exceed `capacity`, no matter how long the bucket sits idle before the next call -- refill must clamp, not accumulate without bound.
2. Refill must account for the *exact* elapsed clock time since the last refill, continuously. Calling `available()` or `try_acquire()` repeatedly across many small advances must credit the same total as one single advance covering the same total elapsed time -- no fractional remainder may be silently dropped at any individual call.
3. `try_acquire(cost)` succeeds, deducting exactly `cost`, if and only if the refilled balance is `>= cost`. On failure, the stored balance must be exactly what refilling alone would have produced -- never partially deducted, and never negative.
4. Two calls at the same clock instant (zero elapsed time) must refill by exactly zero additional tokens.
5. `available()` must never itself grant or consume tokens beyond what elapsed time actually entitles -- it reports the balance a subsequent `try_acquire()` at that same instant would see.

## What's out of scope

Negative `refill_rate` or `capacity`, multi-threaded access, and any persistence across process restarts.

## Deliverable

Copy the complete `ratelimit` package to `/app/submission/ratelimit`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria, each a scripted sequence of `try_acquire`/`available`/clock-advance operations against the actual submitted `TokenBucket` object, driven by a fake clock the submission cannot see or control:

1. **Basic correctness.** Plain consumption and exhaustion with no idle periods or fractional advances. (15%)
2. **Capacity clamp.** An idle period longer than it takes to refill to capacity must not grant more than `capacity` tokens. (25%)
3. **Fractional refill.** Several small, non-integer clock advances must sum to the same credited total as one equivalent large advance. (25%)
4. **Exact accounting.** Boundary-exact `try_acquire` calls (balance exactly equal to cost) and failed calls (balance must stay untouched beyond refill) checked precisely. (20%)
5. **A longer mixed sequence** combining idle bursts, fractional advances, and exact exhaustion, checked at every step. (15%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only the Python standard library is available at verification time; no network access.
