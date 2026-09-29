# Synchronous FIFO

The agent fixes a synchronous FIFO controller's classic simultaneous-full-write-and-read bug: a write issued in the same cycle as a read that frees the last slot of a full FIFO is silently dropped, because the write is gated only on the registered `full` flag without accounting for the concurrent read. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base plus Icarus Verilog and cocotb 2.1.0 -- no real hardware or FPGA is used or required. This is the only task in the set written in Verilog rather than Python; the deliverable is a single `fifo.v` file.

## Grading mechanism

The verifier compiles the submitted `fifo.v` with Icarus Verilog and drives it with a cocotb testbench, cycle by cycle, comparing the module's `full`/`empty`/`rd_data` against an independent Python reference model (`RefModel` in `tests/test_fifo.py`) that implements the same specification from scratch -- never derived from the DUT. Five cocotb test functions map to the five graded criteria; cocotb's own JUnit-style `results.xml` output is parsed directly for pass/fail per test.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic write/read | 15% | In-order correctness, no edge cases |
| Full/empty flags | 20% | Assert at exactly the right occupancy |
| Wraparound | 20% | 120 randomized operations stressing pointer wraparound |
| Simultaneous full write+read | 30% | The core bug: write must succeed when a same-cycle read frees the last slot |
| Simultaneous empty write+read | 15% | Read is a no-op; write still succeeds |

All five are deterministic, cycle-accurate simulation checks (fixed clock, no real concurrency or metastability modeling, seeded randomness for the wraparound stress test) against an independently implemented reference, not source inspection.

## Layout

- `instruction.md`: agent request (431 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the buggy starter `fifo.v`, `TASK_CONTRACT.md`, and a cocotb-based `reproduce.py`/`reproduce_test.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: cocotb testbench (`test_fifo.py`, with the independent reference model), `Makefile`, grader (parses `results.xml`), and Dockerfile.

## Status

Fully validated end-to-end through real Docker containers running the actual Icarus Verilog + cocotb toolchain (not mocked): both images build clean; the oracle solution scores `reward=1`, 5/5, through the real, separate verifier container. The buggy starter scores `0.7`, failing exactly and only the simultaneous-full-write-read criterion while passing basic correctness, flag timing, 120-operation wraparound stress, and the simultaneous-empty case. `reproduce.py` reproduces the bug live: draining the FIFO afterward yields `[1, 2, 3, 4, 5, 6, 7, 7]` -- the value written during the simultaneous cycle never comes back out, and a stale value appears twice instead. Two real cocotb timing bugs were caught and fixed while building this (a ReadOnly-phase write-lock violation, and a race reading registered outputs before non-blocking assignments had settled) -- both fixed with `NextTimeStep()`, a standard cocotb idiom for this exact situation. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief (not run; see root `README.md`). The pre-rollout QC/QA script (the runbook's own `eval_guide.md` rubric + `dq_audit.py`) has since been run against this task and raised no findings.
