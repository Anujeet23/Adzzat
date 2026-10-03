Fix the streaming JSON parser at `/app/repo/jsonstream` so it tracks whether it's currently inside a string literal while scanning for a complete top-level value. The current implementation counts `{`/`[`/`}`/`]` characters anywhere in the buffered text to find where a value ends -- including ones that appear literally inside a string value -- so a value like `{"shape": "{curly}"}` gets cut off (or fails to parse) long before its real end. Read `/app/TASK_CONTRACT.md` before changing anything; `/app/reproduce.py` demonstrates the corruption live.

## Interface

`jsonstream.StreamingParser()` implements `feed(chunk: str) -> list`, which appends `chunk` to an internal buffer and returns a list (possibly empty) of every complete top-level JSON value (object or array) that became fully available as a result of this call, each already parsed into the equivalent Python object (via the standard `json` module's own value semantics). Values are returned in the order they completed; a value that was already complete before this call was never returned again. Whitespace between top-level values is ignored.

## Required guarantees

1. A single JSON value may be split across any number of `feed()` calls, down to one character per call, and must still be parsed correctly and returned exactly once, as soon as it becomes complete.
2. `{`, `}`, `[`, and `]` characters that appear inside a string value must never be mistaken for structural depth changes -- `{"shape": "{curly}"}` is one complete object, not evidence of a premature or malformed end.
3. An escaped quote (`\"`) inside a string must never be mistaken for that string's closing quote.
4. A literal backslash immediately before a closing quote (`\\"`, an escaped backslash followed by a real closing quote) must be told apart from an escaped quote (`\"`) -- escape parity must be tracked correctly, not just "does a `\` appear before this `"`".
5. Multiple complete top-level values arriving back-to-back in the stream, including when two consecutive values are split across the same `feed()` call boundary, must each be returned separately, in order, with none dropped or merged.

## What's out of scope

Top-level scalar values (a bare number, string, or literal with no enclosing `{}`/`[]`), malformed JSON recovery, and any specific chunk size -- chunks may arrive at any granularity, including one character at a time.

## Deliverable

Copy the complete `jsonstream` package to `/app/submission/jsonstream`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria, each a scripted sequence of `feed()` calls against the actual submitted `StreamingParser` object, checking the exact values returned at each call:

1. **Basic correctness.** A few simple values with no special characters, fed in a handful of chunks. (15%)
2. **Braces inside string values.** The core bug: structural characters appearing inside a string must not corrupt depth tracking. (25%)
3. **Byte-at-a-time streaming.** A value containing braces inside a string, fed one character per call. (20%)
4. **Escape handling.** Escaped quotes and escaped backslashes adjacent to brace characters inside a string, including the `\\"` vs `\"` distinction. (25%)
5. **A longer mixed sequence** combining all of the above, with several back-to-back values and arbitrary chunk boundaries. (15%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only the Python standard library is available at verification time; no network access.
