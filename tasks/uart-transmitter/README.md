# UART transmitter

Category: **RTL**. The agent fixes a UART TX whose bit-duration counter reloads one cycle late, so every bit of the 10-bit frame is held one cycle too long and timing drifts across the frame. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base with Icarus Verilog 11 and cocotb 2.1.0 installed from the Debian/PyPI packages; no network access at run time. Grading is real cycle-accurate simulation, not a mock. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

The verifier compiles only the submitted `.v` file with Icarus Verilog and runs a cocotb testbench that drives the module cycle by cycle in lockstep with an independent Python reference model (never derived from the DUT), asserting every output agrees after every cycle. One cocotb test function maps to one criterion, read back from `results.xml`. `CLKS_PER_BIT` is fixed at 4. The testbench samples `tx` at the midpoint of each expected bit slot and checks `tx_busy`/`tx_done` cycle-exactly (busy drops on the same cycle `tx_done` pulses).

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Single-byte bit timing | 20% | every bit sampled at its exact cycle |
| busy/done timing | 25% | exact frame length and `tx_done` cycle |
| Back-to-back frames | 20% | several bytes in sequence |
| Edge-case patterns | 15% | 0x00, 0xFF, alternating bits |
| Mixed random | 20% | randomized bytes with idle gaps |

All five are deterministic and independent. The harness reward is binary (every criterion must pass); the weighted score and per-criterion diagnostics are retained separately.

## Layout

- `instruction.md`: agent request (495 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the unsafe starter `.v` file, `TASK_CONTRACT.md`, `Makefile`, and `reproduce.py`/`reproduce_test.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: cocotb testbench with the Python reference model, grader, and Makefile.

## Status

Validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, through the real, separate verifier container. The naive starter scores `0.0`. `reproduce.py` reproduces the bug live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief (not run; see root `README.md`).

## Pre-rollout QC/QA

Run with the runbook's own `eval_guide.md` rubric and `dq_audit.py` (independent reviewer, task folder minus `solution/`). Reviewer found back-to-back frames always had idle gaps, so guarantee 5 was untested. Fixed: the back-to-back test now issues the next `tx_start` on the cycle `tx_busy` drops; oracle 5/5, naive still fails. The grader stages its own Makefile and testbench and compiles only the submitted `.v`; a hostile Verilog submission could in principle tamper with `results.xml` through simulator system tasks (same limitation as `sync-fifo`). Full merged results for this batch are in `qa/phase2/`.
