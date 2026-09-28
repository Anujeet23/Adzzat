Harden the embedded key-value store skeleton at `/app/repo/kvstore` so it survives an abrupt process kill (`kill -9`, power loss) at any point during a write, delete, or compaction, without losing any acknowledged write, without ever exposing a torn or corrupted record, and without letting corruption block future operations. Read `/app/TASK_CONTRACT.md` for the exact API and durability contract before changing anything; `/app/reproduce.py` demonstrates the current implementation's data-loss bug.

## Interface

`kvstore.KVStore(path)` implements `put(key: bytes, value: bytes)`, `delete(key: bytes)`, `get(key: bytes) -> bytes | None`, `iter_items() -> list[tuple[bytes, bytes]]`, `compact()`, and `close()`.

Every disk write, fsync, atomic rename, and directory fsync that matters for durability must go through `kvstore.iolayer`, called as `iolayer.pwrite_all(...)`, `iolayer.fsync(...)`, `iolayer.atomic_replace(...)`, `iolayer.fsync_dir(...)` via the module reference (`from . import iolayer`), not `from .iolayer import ...`. The grading harness instruments exactly these four entry points to simulate a hard process kill at a chosen point during a call, including a realistic partial write of the in-flight buffer. Writes that bypass `iolayer` are invisible to the harness and cannot count as durable.

## Required guarantees

1. `put`/`delete` must not return until their effect is durable; a kill immediately after either call returns must never lose that write on the next open.
2. A kill during `put`/`delete` must leave the store in exactly the state from before the call, or exactly the state from after it — never a mix, never a corrupted or partial record, and never a state that blocks correctly reading or appending further records afterward.
3. `compact()` never changes the logical key/value contents visible through `get`/`iter_items`; it only repacks storage. A kill at any point during `compact()` must leave the store's logical contents unchanged, and the store must remain fully usable afterward.
4. A reader (`iter_items`, `get`) running in a separate process, concurrently with a `compact()` call on the same directory, must never observe a mix of pre- and post-compaction file state, and must never raise.
5. These properties must keep holding across repeated open/crash/reopen cycles, not just once.

## Deliverable

Copy the complete, working `kvstore` package (including `iolayer.py`, whether or not you changed it) to `/app/submission/kvstore`. The verifier imports only `/app/submission/kvstore` as an unprivileged user in a separate container; it does not read `/app/repo` and installs nothing.

## Verification

Five independent, weighted criteria, each run against real subprocess kills (`os._exit`) and real on-disk state, not the transcript: basic functional correctness (15%); durability of `put`/`delete` under a kill at many different points inside the call (25%); crash safety of `compact()` under a kill at every internal durability call it makes (30%); reader isolation during concurrent compaction (20%); and confirmation that durability-relevant operations are actually routed through `iolayer`'s four entry points (10%). A full pass requires all five; per-criterion outcomes are retained separately for diagnosis.

Only the Python standard library is available at verification time; no network access. Keys and values in the graded scenarios are at most a few kilobytes.
