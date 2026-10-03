# LRU + TTL cache

Category: **Program Bench**. The agent fixes an in-memory cache whose LRU eviction and per-entry TTL expiry don't interact: `get()` never checks expiry (stale reads), never refreshes recency, and eviction ignores already-expired entries. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access. Pure in-memory logic with a fake, caller-controlled clock where time matters, so nothing about real elapsed time is ever graded. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

The verifier never inspects source or reads the agent's transcript. Each criterion is a scripted, fixed sequence of operations (from a JSON fixture) run against the submission's actual objects in an unprivileged subprocess, with every step's expected outcome checked exactly. Time is a fake clock injected by the runner, so expiry is exact and deterministic.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic correctness | 15% | put/get/overwrite, no expiry or eviction pressure |
| TTL expiry | 25% | get() and len() must exclude expired entries |
| LRU recency | 25% | a read key must survive an eviction that would otherwise claim it |
| Expired-first reclaim | 20% | expired entries freed before any live one is evicted |
| Mixed sequence | 15% | expiry, recency and eviction combined, checked each step |

All five are deterministic and independent. The harness reward is binary (every criterion must pass); the weighted score and per-criterion diagnostics are retained separately.

## Layout

- `instruction.md`: agent request (557 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the unsafe starter package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: scripted-op runner, grader, and JSON fixtures.

## Status

Validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, through the real, separate verifier container. The naive starter scores `0.15` (basic correctness only). `reproduce.py` reproduces the bug live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief (not run; see root `README.md`).

## Pre-rollout QC/QA

Run with the runbook's own `eval_guide.md` rubric and `dq_audit.py` (independent reviewer, task folder minus `solution/`). Reviewer found no fixture covered overwrite-resets-expiry or `len()` excluding not-yet-purged expired entries. Fixed: `ttl_expiry.json` now covers both; oracle still 5/5, naive still fails. Full merged results for this batch are in `qa/phase2/`.
