# Incremental topological sort

Category: **Program Bench**. The agent fixes an incrementally built DAG that only rejects a direct two-node cycle (longer cycles and self-loops slip through) and whose `order()` returns stale insertion order. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access. Pure in-memory logic with a fake, caller-controlled clock where time matters, so nothing about real elapsed time is ever graded. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

The verifier never inspects source or reads the agent's transcript. Each criterion is a scripted, fixed sequence of operations (from a JSON fixture) run against the submission's actual objects in an unprivileged subprocess, with every step's expected outcome checked exactly. `order()` is validated by property (a permutation of the known nodes, every edge u->v with u before v) against a node/edge set the runner tracks itself, so any valid topological order is accepted.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic correctness | 15% | chain built in compatible order |
| Longer-cycle detection | 25% | closing edge of a 3+-edge cycle rejected |
| Order consistency | 25% | insertion order must be overridden by later edges |
| Rejection leaves graph unchanged | 20% | longer cycle and self-loop |
| Mixed sequence | 15% | combined, checked at multiple points |

All five are deterministic and independent. The harness reward is binary (every criterion must pass); the weighted score and per-criterion diagnostics are retained separately.

## Layout

- `instruction.md`: agent request (510 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the unsafe starter package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: scripted-op runner, grader, and JSON fixtures.

## Status

Validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, through the real, separate verifier container. The naive starter scores `0.15`. `reproduce.py` reproduces the bug live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief (not run; see root `README.md`).

## Pre-rollout QC/QA

Run with the runbook's own `eval_guide.md` rubric and `dq_audit.py` (independent reviewer, task folder minus `solution/`). Reviewer found `reject_unchanged.json` could not detect a phantom edge left behind by a rejected call. Fixed: it now adds `p -> r` after the rejected `r -> p`, which a leftover phantom edge would wrongly reject; oracle 5/5, naive still fails. Full merged results for this batch are in `qa/phase2/`.
