# Crash-safe embedded key-value store — contract

Source: an original, minimal starter at `/app/repo/kvstore`, not a fork of an existing project.

## API

`kvstore.KVStore(path: str)`:

- `put(key: bytes, value: bytes) -> None` — must not return until the write is durable.
- `delete(key: bytes) -> None` — same durability requirement; a deleted key must not reappear after any later crash/recovery.
- `get(key: bytes) -> bytes | None`
- `iter_items() -> list[tuple[bytes, bytes]]`
- `compact() -> None` — repacks storage; never changes the logical key/value set visible through `get`/`iter_items`.
- `close() -> None`

Keys and values are arbitrary byte strings up to a few kilobytes in the graded scenarios. The on-disk format is entirely up to you.

## Durability instrumentation

`kvstore.iolayer` exposes four functions: `pwrite_all(fd, data)`, `fsync(fd)`, `atomic_replace(src, dst)`, `fsync_dir(dir_path)`. Every write, fsync, rename, and directory-fsync that must be durable for `put`, `delete`, or `compact` to satisfy the guarantees below must go through these functions, called as `iolayer.<name>(...)` via the module object (`from . import iolayer`), not via `from .iolayer import <name>`.

The grading harness replaces these four attributes on the `iolayer` module object with instrumented wrappers before running your code, and can kill the process (`os._exit`) at an exact call, including performing only a random-length partial write of the buffer passed to `pwrite_all` before dying (this models a real torn write / partial sector write). Any durability-relevant I/O performed outside these four functions is invisible to that instrumentation: it will run to completion even in a "crash" scenario, which means the corresponding guarantee cannot be verified as satisfied and is graded as unmet.

## Guarantees

1. **Acknowledged durability.** Once `put`/`delete` returns, its effect survives an immediate kill.
2. **All-or-nothing per call.** A kill during `put`/`delete` leaves the store exactly as it was immediately before that call, or exactly as it would be immediately after — never a corrupted/partial record, and never a state where a subsequent, fully-completed `put` becomes unreadable because of leftover garbage from the interrupted one.
3. **Compaction is logically a no-op.** `compact()` only repacks physical storage. A kill at any point during `compact()` must leave `get`/`iter_items` results identical to what they were immediately before `compact()` was called, and the store must remain fully readable and writable afterward.
4. **Reader isolation.** A separate process calling `iter_items()`/`get()` on the same directory while another process is inside `compact()` must see either the pre-compaction or the post-compaction state in full — never a mix — and must never raise.
5. **Recovery is stable.** These properties must hold after repeated open/crash/reopen cycles, not just once.

## What's out of scope

Multiple concurrent writers, a networked or multi-node store, transactions spanning multiple keys, and any specific on-disk byte layout. None of these are tested.

## Delivery

Copy the complete `kvstore` package (including your `iolayer.py`, whether or not you changed it) to `/app/submission/kvstore`. The verifier container imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and does not install any additional dependency — only the Python standard library is available at verification time.
