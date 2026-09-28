# Fast matrix multiplication

The agent replaces an O(n^3) triple-loop matrix multiplication with an asymptotically faster algorithm (Strassen's, or equivalent), graded by *counting scalar multiplications*, never wall-clock time -- so the result is fully deterministic and immune to machine load or timing noise. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access, no numerical libraries. No GPU is used or required -- this is a single-threaded, CPU-only algorithmic problem. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

Every scalar multiplication the submission's `matmul` performs, at any recursion depth, must go through `kernel.ops.mul`, called via the module reference so the grading harness can replace that one attribute with a counting wrapper (the same instrumentation pattern as this project's crash-safe-kv-store task, applied to arithmetic instead of I/O). The harness never measures wall-clock time; it checks that the multiplication count grows by meaningfully less than 8x when matrix size doubles -- the signature of any `O(n^3)` algorithm -- as a *ratio* between doubled sizes, so the check doesn't depend on any particular constant-factor implementation detail, only on genuine sub-cubic scaling.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Correctness, n=8 | 20% | Baseline correctness against an independent reference |
| Correctness, n=64 | 15% | Correctness holds at a larger size too |
| Growth ratio 16→32 | 25% | Must stay below 7.5x (naive shows exactly 8.0x) |
| Growth ratio 32→64 | 25% | Same check at the next doubling |
| Absolute bound at n=16 | 15% | Closes the loophole of gaming the ratio alone |

All five are exact, deterministic checks computed from a single instrumented call per fixture size -- no timing, no repeated-run averaging, no flakiness.

## Layout

- `instruction.md`: agent request (375 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the O(n^3) starter `kernel` package (including the shared `ops.py` counting primitive), `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation (Strassen's algorithm) and installation script.
- `tests/`: runner (instruments `ops.mul`, reports counts), grader (independent correctness reference + ratio checks), and fixtures (deterministic random matrices at n=8/16/32/64).

## Status

Fully validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, in about 2 seconds through the real, separate verifier container, with multiplication counts matching Strassen's theoretical `7^log2(n)` exactly (2401, 16807, 117649 at n=16/32/64 -- a clean 7.0x ratio at every doubling). The triple-loop starter scores `0.35`, passing both correctness checks (it's a valid algorithm) and failing all three efficiency checks with an exact 8.0x ratio at every doubling. `reproduce.py` reproduces the 8x signature live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief, and the QC/QA script once it's provided.
