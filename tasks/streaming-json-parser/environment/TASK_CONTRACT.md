# Streaming JSON parser — contract

Source: an original, minimal starter at `/app/repo/jsonstream`, not a fork of an existing project.

## API

```python
class StreamingParser:
    def feed(self, chunk: str) -> list: ...
```

`feed` appends `chunk` to an internal buffer and returns every complete top-level JSON value (object `{...}` or array `[...]`) that became fully available as a result of this call, parsed into the equivalent Python object, in the order they completed. Whitespace between top-level values is ignored. Only object/array top-level values are in scope.

## Guarantees

1. **Arbitrary chunking.** A value may be split across any number of `feed()` calls, down to one character per call, and is returned exactly once, as soon as it is complete.
2. **String-aware depth tracking.** `{`, `}`, `[`, `]` characters inside a string value never affect structural depth counting.
3. **Escaped quotes.** `\"` inside a string never closes that string.
4. **Escape parity.** A literal backslash immediately before a closing quote (`\\"`) is distinguished from an escaped quote (`\"`) by tracking whether the preceding backslash was itself already consumed as an escape, not just by checking whether a `\` immediately precedes the `"`.
5. **Back-to-back values.** Consecutive top-level values in the stream, even when split across the same `feed()` call boundary, are each returned separately, in order, with none dropped or merged.

## What's out of scope

Top-level scalar values, malformed-JSON recovery, and any specific chunk granularity.

## Delivery

Copy the complete `jsonstream` package to `/app/submission/jsonstream`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
