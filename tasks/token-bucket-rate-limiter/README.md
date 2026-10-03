# Token-bucket rate limiter

Category: **Program Bench**. The agent fixes a token bucket whose refill math truncates elapsed time to whole units (silently losing fractional refill) and never clamps the balance to capacity. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access. Pure in-memory logic with a fake, caller-controlled clock where time matters, so nothing about real elapsed time is ever graded. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

The verifier never inspects source or reads the agent's transcript. Each criterion is a scripted, fixed sequence of operations (from a JSON fixture) run against the submission's actual objects in an unprivileged subprocess, with every step's expected outcome checked exactly. Fake clock again; float balances are compared within 1e-6.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic correctness | 15% | plain consumption/exhaustion |
| Capacity clamp | 25% | long idle must not exceed capacity |
| Fractional refill | 25% | many small advances credit the same total as one large one |
| Exact accounting | 20% | boundary-exact acquires, no partial deduction on failure |
| Mixed sequence | 15% | idle bursts, fractional advances and exhaustion combined |

All five are deterministic and independent. The harness reward is binary (every criterion must pass); the weighted score and per-criterion diagnostics are retained separately.

## Layout

- `instruction.md`: agent request (524 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the unsafe starter package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: scripted-op runner, grader, and JSON fixtures.

## Status

Validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, through the real, separate verifier container. The naive starter scores `0.15`. `reproduce.py` reproduces the bug live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief (not run; see root `README.md`).

## Pre-rollout QC/QA

Run with the runbook's own `eval_guide.md` rubric and `dq_audit.py` (independent reviewer, task folder minus `solution/`). No grading bypass. Coverage is thin (no zero-elapsed repeat calls, no non-unit refill rate); disclosed, not changed. Full merged results for this batch are in `qa/phase2/`.
