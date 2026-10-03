# SPSC ring buffer

Category: **Program Bench**. The agent fixes a fixed-capacity ring buffer that tracks only head/tail indices, so `push` never checks capacity (silently overwriting unread data) and a full buffer reports the same length as an empty one. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access. Pure in-memory logic with a fake, caller-controlled clock where time matters, so nothing about real elapsed time is ever graded. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

The verifier never inspects source or reads the agent's transcript. Each criterion is a scripted, fixed sequence of operations (from a JSON fixture) run against the submission's actual objects in an unprivileged subprocess, with every step's expected outcome checked exactly. Grading is a single-threaded scripted push/pop sequence; no real threads or timing, which keeps it deterministic.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic correctness | 15% | push/pop below capacity |
| Full-buffer rejection | 25% | push on a full buffer fails without corrupting data |
| Empty-buffer rejection | 15% | pop on empty raises |
| Wraparound integrity | 25% | many fill/reject/drain cycles |
| Mixed sequence | 20% | all of the above, checked every step |

All five are deterministic and independent. The harness reward is binary (every criterion must pass); the weighted score and per-criterion diagnostics are retained separately.

## Layout

- `instruction.md`: agent request (460 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the unsafe starter package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: scripted-op runner, grader, and JSON fixtures.

## Status

Validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, through the real, separate verifier container. The naive starter scores `0.15`; even the basic fixture trips the full/empty length ambiguity once the buffer fills exactly. `reproduce.py` reproduces the bug live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief (not run; see root `README.md`).

## Pre-rollout QC/QA

Run with the runbook's own `eval_guide.md` rubric and `dq_audit.py` (independent reviewer, task folder minus `solution/`). No grading bypass. Fixtures are small (capacity 2-4); capacity 1 and falsy items are not exercised. Disclosed. Full merged results for this batch are in `qa/phase2/`.
