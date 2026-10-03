# Direct-mapped cache controller

Category: **Chip Design**. The agent fixes a direct-mapped cache controller that overwrites a dirty line on a miss without writing it back to the backing store first, silently losing the write. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base with Icarus Verilog 11 and cocotb 2.1.0 installed from the Debian/PyPI packages; no network access at run time. Grading is real cycle-accurate simulation, not a mock. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

The verifier compiles only the submitted `.v` file with Icarus Verilog and runs a cocotb testbench that drives the module cycle by cycle in lockstep with an independent Python reference model (never derived from the DUT), asserting every output agrees after every cycle. One cocotb test function maps to one criterion, read back from `results.xml`. Every check goes through the external `req/we/addr/wdata/hit/rdata` interface only; write-back is observed by evicting a dirty line and re-fetching its address. All tests share one simulation and `rst_n` never clears the backing store, so each test uses a disjoint address range (an isolation bug caught while building this task).

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic hit/miss | 15% | cold miss with seeded data, repeat hit |
| Write then read hit | 15% | written value, not stale seed |
| Dirty write-back on eviction | 35% | evicted dirty data visible on re-fetch |
| Clean eviction | 10% | no write-back needed, seed value intact |
| Mixed random | 25% | random reads/writes over colliding addresses vs the model |

All five are deterministic and independent. The harness reward is binary (every criterion must pass); the weighted score and per-criterion diagnostics are retained separately.

## Layout

- `instruction.md`: agent request (598 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the unsafe starter `.v` file, `TASK_CONTRACT.md`, `Makefile`, and `reproduce.py`/`reproduce_test.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: cocotb testbench with the Python reference model, grader, and Makefile.

## Status

Validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, through the real, separate verifier container. The naive starter scores `0.40`: it passes the three criteria that don't depend on write-back. `reproduce.py` reproduces the bug live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief (not run; see root `README.md`).

## Pre-rollout QC/QA

Run with the runbook's own `eval_guide.md` rubric and `dq_audit.py` (independent reviewer, task folder minus `solution/`). Sound. `done` and `req`-gating (guarantee 5) are not tested, and a design that always writes back on eviction would still pass the clean-eviction test. Disclosed. The grader stages its own Makefile and testbench and compiles only the submitted `.v`; a hostile Verilog submission could in principle tamper with `results.xml` through simulator system tasks (same limitation as `sync-fifo`). Full merged results for this batch are in `qa/phase2/`.
