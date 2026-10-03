Make the bounded cache at `/app/repo/cache` correctly combine two eviction mechanisms that currently don't interact at all: least-recently-used (LRU) capacity eviction, and per-entry time-to-live (TTL) expiry. Read `/app/TASK_CONTRACT.md` for the exact API and guarantees before changing anything; `/app/reproduce.py` demonstrates a stale read and an incorrect eviction with the current implementation.

## Interface

`cache.TTLCache(max_size, clock=None)` implements `put(key, value, ttl)` and `get(key)` (raises `KeyError` on a missing or expired key) and `__len__()` (the number of currently live, non-expired entries). `ttl` is a number of clock units until that entry expires, measured from the moment of that `put()` call. `clock` is a zero-argument callable returning the current time as a number; it defaults to a real wall clock, but the verifier always supplies its own fake, caller-controlled one, so nothing about real elapsed time is ever graded.

## Required guarantees

1. `get(key)` must raise `KeyError` for a key that was never put, was evicted for capacity, or whose `ttl` has elapsed (checked against the clock at the moment of that `get()` call) since it was put or last overwritten -- never return a stale value.
2. A successful `get(key)` counts as a use: immediately afterward, that key must be the least likely to be evicted next of all currently live keys, exactly as if it had just been `put` again.
3. When inserting a new key would exceed `max_size` live entries, eviction must free room from already-expired entries first; only if that is still not enough may it evict the least-recently-used *live* entry (by the recency order in guarantee 2). An expired entry must never be preferred for survival over a live one.
4. Overwriting an existing key via `put()` resets both its value and its expiry baseline to the clock's value at that call, and counts as the most-recent use of that key.
5. `len(cache)` always reports the number of currently live entries -- an expired entry must never be counted, whether or not it has been physically purged yet.

## What's out of scope

Negative or zero `ttl`, concurrent access from multiple threads, and any persistence across process restarts -- this is a single-threaded, in-memory cache.

## Deliverable

Copy the complete `cache` package to `/app/submission/cache`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria, each run as a scripted sequence of `put`/`get`/clock-advance operations against the actual submitted `TTLCache` object, with a verifier-controlled fake clock (never real time):

1. **Basic correctness.** `put`/`get`/overwrite with no expiry or capacity pressure. (15%)
2. **TTL expiry is enforced.** A `get()` on an expired key must miss, and `len()` must exclude it, even before anything has triggered a physical purge. (25%)
3. **LRU recency follows reads, not just writes.** A key read since its last write must survive an eviction that would otherwise have claimed it. (25%)
4. **Expired entries are reclaimed before live ones.** Inserting past capacity must never evict a live entry while an already-expired one still occupies a slot. (20%)
5. **A longer mixed sequence** combining expiry, recency, and eviction, checked at each step. (15%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only the Python standard library is available at verification time; no network access.
