# Crash-safe embedded key-value store

The agent hardens a deliberately unsafe embedded key-value store (no checksums, no fsync, in-place non-atomic compaction) into one that survives a hard process kill at any point, including mid-compaction, without losing acknowledged writes, exposing torn records, or letting a corrupted tail silently swallow later, fully-successful writes. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md) for the API and durability contract.

## Environment

Both images use a digest-pinned Python 3.12.11 Debian Bookworm base. No native dependencies, no network access, no GPU. The agent image contains the starter package, the contract, and a script reproducing the current data-loss bug. Agent and verifier each receive two CPU cores and 2 GiB RAM; the agent has four hours and the verifier fifty minutes.

## Grading mechanism

The verifier never inspects the submission's source or relies on the agent's transcript. It replaces the four functions in the submission's own `kvstore.iolayer` module with instrumented wrappers, runs a scripted sequence of `put`/`delete`/`compact` calls against the submitted `KVStore` in a subprocess, and can kill that subprocess (`os._exit`) at an exact instrumented call -- including writing only a random-length partial prefix of the buffer passed to `pwrite_all` before dying, to model a real torn write. After the kill, a fresh subprocess reopens the store and reports its logical contents, which the grader checks against the only two states that should ever be possible: the state immediately before the interrupted call, or the state immediately after it. For `compact()`, both of those states are required to be identical, since compaction must never change logical content. A separate mode pauses the writer synchronously (no real concurrency, no timing race) at each of the same call points and runs a second, unmodified reader subprocess against the same directory to check it never observes a torn mix of pre- and post-compaction file state.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic correctness | 15% | put/get/delete/overwrite/compact/reopen, no crashes |
| Durability | 25% | Kill at many points inside every put/delete, across the whole sequence |
| Crash-safe compaction | 30% | Kill at every durability call compact() makes |
| Reader isolation | 20% | Concurrent reader during compaction, paused at every call compact() makes |
| Contract compliance | 10% | Durability-relevant work is actually routed through `iolayer` |

All five are independent, deterministic, and reproducible: no real threads, no real signal races, no network. The harness reward is binary -- every criterion must pass -- with the weighted score and per-criterion diagnostics retained separately.

## Layout

- `instruction.md`: agent request (482 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the unsafe starter `kvstore` package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: fault-injecting worker, recovery/reader checker, grader, and fixtures.

## Status

Fully validated end-to-end through real Docker containers (`crash-safe-kv-store-env` / `crash-safe-kv-store-tests`): both images build clean; the oracle solution (`solution/store.py`) scores `reward=1`, 5/5 criteria, through the real, separate verifier container, across 16 durability crash points and 6 compaction crash/pause points. The unsafe starter (`environment/kvstore/store.py`, what agents actually start from) scores `0.15` (criterion 1 only) -- it never routes writes through `iolayer`, so every durability/compaction/reader-isolation/compliance check correctly fails. A deliberately partial implementation (correct fsync'd durability, but an unsafe in-place `compact()`) scores `0.40` (criteria 1-2 pass, 3-5 fail) -- confirming the five criteria are independently gradable and don't collapse to one pass/fail band, which is what the score-distribution requirement is actually checking for. `environment/reproduce.py` reproduces the starter's data-loss bug and is confirmed silent (no data loss) against the reference solution.

**Pre-rollout QC/QA (run; disclosed, not fixed):** the runbook's own `eval_guide.md` rubric + `dq_audit.py` flagged two real limitations, both structural rather than one-line bugs, so left as disclosed risk rather than patched:

1. Rubric 5 ("contract compliance") overclaims relative to what `grade.py`'s check actually does: it only verifies that at least one `iolayer` call of the expected kind occurred per operation, not that the bulk of the durability-critical I/O was routed through `iolayer` rather than raw `os.*` calls. A submission making one decorative `iolayer` call per op while doing its real I/O elsewhere would still pass this 10%-weighted criterion.
2. The crash injection (`crash_worker.py`) kills the writer subprocess via `os._exit()` in the same OS/container as the grader, not a real power loss or page-cache drop. When the kill lands on an `fsync`/`atomic_replace`/`fsync_dir` call, the preceding writes are typically still resident in the OS page cache and visible to the "fresh" recovery subprocess regardless of whether the fsync/rename actually ran -- so the 25%/30%-weighted durability and compaction criteria are somewhat weaker evidence of true power-loss durability than their description implies, though they do still catch torn-write and ordering bugs via the partial-write injection.

Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 (pass-rate ≤2/5, bimodal score spread, 100+ step count for a successful rollout) required by the author brief (not run; see root `README.md`).
