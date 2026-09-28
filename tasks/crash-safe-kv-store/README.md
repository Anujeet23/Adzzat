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

Validated so far, running the grader directly against `python3` (not yet inside Docker, since no container runtime was available in the authoring environment):

- The reference solution (`solution/store.py`) scores `reward=1`, 5/5 criteria, across 16 durability crash points and 6 compaction crash/pause points.
- The unsafe starter (`environment/kvstore/store.py`, what agents actually start from) scores `0.15` (criterion 1 only) -- it never routes writes through `iolayer`, so every durability/compaction/reader-isolation/compliance check correctly fails.
- A deliberately partial implementation (correct fsync'd durability, but an unsafe in-place `compact()`) scores `0.40` (criteria 1-2 pass, 3-5 fail) -- confirming the five criteria are independently gradable and don't collapse to one pass/fail band, which is what the score-distribution requirement is actually checking for.
- `environment/reproduce.py` reproduces the starter's data-loss bug and is confirmed silent (no data loss) against the reference solution.

Still outstanding before this is submission-ready:

1. Build and run both Dockerfiles for real (this dev machine had no container runtime; grading was run directly against the same Python files instead).
2. Collect the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief (pass-rate ≤2/5, bimodal score spread, 100+ step count for a successful rollout) -- this needs Harbor/Terminal-Bench plus live model access, neither of which is available here yet.
3. Run the QC/QA script once it's provided.
