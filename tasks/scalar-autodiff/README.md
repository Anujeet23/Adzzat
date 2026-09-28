# Scalar autodiff engine

The agent fixes a reverse-mode autodiff engine that computes correct gradients only when every `Value` is used exactly once -- the classic "overwrite instead of accumulate" bug that breaks as soon as a value feeds into more than one downstream operation. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access, no ML libraries -- this is a from-scratch engine, not a PyTorch/JAX wrapper. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

Every check builds a computation graph with the submission's own `Value` class, calls `.backward()`, and compares each leaf's `.grad` against a central-difference numerical gradient of an independently, plainly-implemented mirror of the same mathematical function (using `math.tanh`/`math.exp` directly, never the submission's forward values) -- so a submission cannot pass by special-casing anything about its own internals. The five fixtures range from graphs with no value reuse at all up to a small mixed network where two inputs each feed two hidden units.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Simple chain | 15% | Every value used exactly once |
| Diamond graph | 30% | A single value used by two operations -- direct accumulation test |
| Loop-built graph | 20% | Graph constructed inside a Python `for` loop over several leaves |
| Nonlinear + reuse | 20% | `relu`/`tanh`/`exp` mixed with a reused intermediate value |
| Mixed integration | 15% | 2-input, 2-hidden-unit scalar network; all 11 leaf gradients checked |

All five are deterministic (central-difference tolerance, no randomness, no timing).

## Layout

- `instruction.md`: agent request (387 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the overwrite-bug starter `autodiff` package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation (same op set, accumulating `+=`) and installation script.
- `tests/`: runner (builds graphs with the submission's `Value`), grader (independent float mirror + central difference), and fixtures.

## Status

Fully validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, on the first run through the real, separate verifier container, matching central-difference gradients to roughly 1e-8 on every leaf across all five fixtures. The overwrite-bug starter scores `0.3`, passing exactly the two fixtures where no value is reused (chain, loop-built) and failing the three that depend on gradient accumulation (diamond, nonlinear-with-reuse, mixed MLP). `reproduce.py` reproduces the accumulation bug live (`x.grad=4.0` vs the true `16.0` for `y = x**2 + x**3` at `x=2`). Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief, and the QC/QA script once it's provided.
