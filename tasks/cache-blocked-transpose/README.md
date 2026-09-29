# Cache-blocked transpose

The agent replaces a cache-thrashing matrix transpose (reads row-major, writes at a stride of `n`) with a cache-blocked (tiled) one, graded by counting misses in a deterministic simulated cache, never wall-clock time. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access, no numerical libraries. No GPU is used or required -- single-threaded, CPU-only. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

Every element access the submission's `transpose` performs must go through `kernel.mem.read`/`kernel.mem.write`, called via the module reference so the grading harness's simulated LRU cache (fixed line size, fixed line count, shared across both the source and destination arrays) can observe it -- the same instrumentation-not-timing pattern used across this project's kernel-optimization tasks. The harness checks both the ratio of miss-count growth as `n` doubles past the point where the matrix no longer fits in the simulated cache, and absolute miss-count bounds at two sizes -- never a wall-clock measurement, so the result is immune to machine load or scheduling noise.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Correctness, n=16 | 20% | Fits entirely in the simulated cache |
| Correctness, n=64 | 15% | Does not fit; algorithm must still be right, not just fast |
| Miss growth ratio 32→64 | 25% | Must stay below 6x (naive shows 18x) |
| Absolute bound at n=64 | 25% | Closes the loophole of gaming the ratio alone |
| Absolute bound at n=128 | 15% | Confirms the bound holds at a larger scale |

All five are exact, deterministic checks computed from a single instrumented call per fixture size -- no timing, no repeated-run averaging, no flakiness.

## Layout

- `instruction.md`: agent request (368 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the thrashing starter `kernel` package (including the shared `mem.py` simulated-cache primitive), `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation (8x8 tiled transpose) and installation script.
- `tests/`: runner (drives `transpose` via the submission's own `mem` simulator), grader (independent correctness reference + ratio/bound checks), and fixtures (n=16/32/64/128).

## Status

Fully validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, through the real, separate verifier container, with miss counts matching the calibration run exactly (256/1024/4096 at n=32/64/128, a clean 4.0x ratio at every doubling past the cache-capacity threshold). The row-major/column-major-mismatch starter scores `0.35`, passing both correctness checks and failing all three efficiency checks with an 18x miss-count jump from n=32 to n=64. `reproduce.py` reproduces that jump live.

**Hardening (post pre-rollout QA):** the original grader trusted the submission's own `kernel/mem.py` for its `stats()` miss/access counting -- a submission could ship a `mem.py` that always self-reports a favorable (e.g. zero-miss) `stats()` regardless of actual access pattern, identical to the `fast-matmul` ops.py exploit. Fixed the same way: the verifier now always substitutes its own trusted `kernel/mem.py` over whatever the submission provided before importing, so a submitted `mem.py` is inert; only `kernel/transpose.py` is graded. Re-validated in Docker after the fix: oracle still 5/5, naive starter still correctly fails criteria 3-5, and an explicit self-reporting cheat (`stats()` hardcoded to `{"misses": 0, "accesses": 1}`) now scores identically to the naive starter (`0.35`, real measured miss counts) instead of gaming a 5/5.

Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief (not run; see root `README.md`).
