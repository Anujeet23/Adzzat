# Robust polynomial root finder

The agent replaces a real-only Newton's-method root finder with one that reliably finds all roots -- real, complex, clustered, or exactly repeated -- of a real-coefficient polynomial, using only the Python standard library (no numpy/scipy in either image, so the numerics can't be shortcut by a library call). See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access, no numerical libraries. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

Every test polynomial is constructed from a known, exact set of roots (some real, some complex-conjugate pairs, some clustered within 0.001 of each other, one with exact multiplicity 4). The verifier never trusts the submission's own claims: for each returned value it independently re-evaluates the polynomial via Horner's method and checks the residual is small relative to the coefficient scale at that magnitude, *and* separately finds the best one-to-one matching between the returned values and the true roots (exact via permutation search for the small degrees used here) and requires every matched pair to be within a stated distance. A solution that collapses a cluster of close roots onto fewer distinct values fails the matching check even if the residual check alone wouldn't catch it.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Well-separated real roots | 15% | Baseline correctness |
| Real coefficients, complex roots | 20% | Must search the complex plane, not just the real line |
| Clustered near-degenerate roots | 25% | Roots within 0.001 of each other |
| Exact high-multiplicity root | 25% | Derivative also vanishes at the root; simple Newton converges only linearly |
| Mixed batch | 15% | Three polynomials combining the above, in one run |

All five are deterministic (no timing, no randomness in fixture generation) and check real numerical behavior against independently-computed ground truth, not source inspection or transcript review.

## Layout

- `instruction.md`: agent request (398 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the real-only starter `rootfind` package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation (Durand-Kerner simultaneous iteration) and installation script.
- `tests/`: runner, grader (independent residual + optimal-matching checks), and fixtures.

## Status

Fully validated end-to-end through real Docker containers: both images build clean; the oracle solution (Durand-Kerner, pure Python) scores `reward=1`, 5/5, on the first run through the real, separate verifier container; the real-only starter scores `0.5`, failing exactly where it should (it cannot find complex roots at all, and happens to hit an unlucky zero-derivative starting point on two of the real-root fixtures) while still passing the clustered and high-multiplicity cases; `reproduce.py` reproduces the complex-root blindness live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief, and the QC/QA script once it's provided.
