# Streaming JSON parser

Category: **Program Bench**. The agent fixes a streaming JSON value extractor that counts braces anywhere in the buffer, including inside string literals, so unbalanced braces in string values corrupt depth tracking. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access. Pure in-memory logic with a fake, caller-controlled clock where time matters, so nothing about real elapsed time is ever graded. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

The verifier never inspects source or reads the agent's transcript. Each criterion is a scripted, fixed sequence of operations (from a JSON fixture) run against the submission's actual objects in an unprivileged subprocess, with every step's expected outcome checked exactly. Fixtures are generated with `json.dumps` to guarantee correct nested escaping, and use *unbalanced* braces inside strings: balanced pairs would let the naive counter land on the right end by coincidence (that mistake was caught and fixed while building this task).

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic correctness | 15% | simple values, few chunks |
| Braces inside strings | 25% | unbalanced `{`/`]` in string values |
| Byte-at-a-time | 20% | one character per feed() call |
| Escape handling | 25% | escaped quotes and `\\"` parity next to braces |
| Mixed sequence | 15% | back-to-back values split across chunk boundaries |

All five are deterministic and independent. The harness reward is binary (every criterion must pass); the weighted score and per-criterion diagnostics are retained separately.

## Layout

- `instruction.md`: agent request (563 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the unsafe starter package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: scripted-op runner, grader, and JSON fixtures.

## Status

Validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, through the real, separate verifier container. The naive starter scores `0.15`. `reproduce.py` reproduces the bug live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief (not run; see root `README.md`).

## Pre-rollout QC/QA

Run with the runbook's own `eval_guide.md` rubric and `dq_audit.py` (independent reviewer, task folder minus `solution/`). Fixtures are thin (no escape split across a chunk boundary, no nesting or top-level arrays). Disclosed. Like the first ten Python tasks, the runner shares a process with the submission and trusts a result file in a scratch directory, so a deliberately malicious submission could forge it; accepted and documented. Full merged results for this batch are in `qa/phase2/`.
