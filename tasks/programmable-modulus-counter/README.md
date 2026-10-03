# Programmable-modulus counter

Category: **RTL**. The agent fixes a counter that counts `modulus + 1` values before wrapping and doesn't reset the count when a new modulus is loaded. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base with Icarus Verilog 11 and cocotb 2.1.0 installed from the Debian/PyPI packages; no network access at run time. Grading is real cycle-accurate simulation, not a mock. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

The verifier compiles only the submitted `.v` file with Icarus Verilog and runs a cocotb testbench that drives the module cycle by cycle in lockstep with an independent Python reference model (never derived from the DUT), asserting every output agrees after every cycle. One cocotb test function maps to one criterion, read back from `results.xml`. 

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic counting | 15% | fixed modulus across several wraps |
| Load resets count | 25% | stale count discarded on a modulus change |
| Overflow timing | 20% | exact overflow cycle across moduli 4, 1 and 6 |
| Pause and resume | 20% | state holds exactly while `en` is low |
| Mixed random | 20% | randomized load/enable sequence |

All five are deterministic and independent. The harness reward is binary (every criterion must pass); the weighted score and per-criterion diagnostics are retained separately.

## Layout

- `instruction.md`: agent request (474 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the unsafe starter `.v` file, `TASK_CONTRACT.md`, `Makefile`, and `reproduce.py`/`reproduce_test.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: cocotb testbench with the Python reference model, grader, and Makefile.

## Status

Validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, through the real, separate verifier container. The naive starter scores `0.0`: both bugs are pervasive enough to break every scenario. `reproduce.py` reproduces the bug live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief (not run; see root `README.md`).

## Pre-rollout QC/QA

Run with the runbook's own `eval_guide.md` rubric and `dq_audit.py` (independent reviewer, task folder minus `solution/`). Reviewer found the spec said `overflow` holds while paused but the model (correctly) keeps it a one-cycle pulse. Fixed: instruction and contract now say `overflow` is low while paused. The grader stages its own Makefile and testbench and compiles only the submitted `.v`; a hostile Verilog submission could in principle tamper with `results.xml` through simulator system tasks (same limitation as `sync-fifo`). Full merged results for this batch are in `qa/phase2/`.
