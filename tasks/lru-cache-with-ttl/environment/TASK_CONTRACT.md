# LRU + TTL cache — contract

Source: an original, minimal starter at `/app/repo/cache`, not a fork of an existing project.

## API

```python
class TTLCache:
    def __init__(self, max_size: int, clock=None): ...
    def put(self, key, value, ttl: float) -> None: ...
    def get(self, key):  # raises KeyError on miss or expiry
        ...
    def __len__(self) -> int: ...
```

`clock` is a zero-argument callable returning the current time as a number (defaults to `time.monotonic`); the verifier always supplies its own fake, caller-controlled clock, so real elapsed time is never part of grading. `ttl` is a positive number of clock units from the moment of that `put()` call.

## Guarantees

1. **No stale reads.** `get(key)` raises `KeyError` for a key that was never put, was evicted, or whose `ttl` has elapsed (checked against the clock at the moment of that `get()` call) since it was put or last overwritten.
2. **Reads refresh recency.** A successful `get(key)` counts as a use: immediately afterward, that key is the least likely of all currently live keys to be evicted next, exactly as if it had just been `put` again.
3. **Expired entries go first.** When inserting a new key would exceed `max_size` live entries, eviction must free room from already-expired entries before evicting any live one; it falls back to evicting the least-recently-used live entry only once no expired entry remains to reclaim.
4. **Overwrite resets both value and expiry.** `put()` on an existing key replaces its value, resets its expiry baseline to the clock's current value, and counts as the most-recent use of that key.
5. **Length excludes expired entries.** `len(cache)` always reports the count of currently live entries, never an expired one, whether or not it has been physically purged yet.

## What's out of scope

Zero or negative `ttl`, multi-threaded access, and persistence across process restarts.

## Delivery

Copy the complete `cache` package to `/app/submission/cache`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
