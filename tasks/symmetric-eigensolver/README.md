# Symmetric eigensolver

The agent replaces a power-iteration-plus-deflation eigensolver with one that reliably finds all eigenvalues and an orthonormal eigenvector basis of a real symmetric matrix, including clustered or exactly repeated eigenvalues, using only the Python standard library. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access, no numerical libraries. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

Every test matrix is constructed from a known, exact eigendecomposition (eigenvalues plus an orthonormal basis built via Gram-Schmidt). The verifier never trusts the submission's own claims: it matches returned eigenvalues optimally against the true ones, then independently recomputes `A @ v` for every returned eigenvector and checks the residual against `lambda * v`, checks each vector is unit norm, and checks the full returned set is mutually orthogonal. Eigenvector *direction* is deliberately not compared to the reference basis when an eigenvalue is repeated -- any orthonormal basis of that eigenspace is mathematically valid, so only the residual and orthogonality checks apply there.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Well-separated eigenvalues | 15% | Baseline correctness |
| Clustered eigenvalues | 25% | Two eigenvalues 0.001 apart |
| Exact repeated eigenvalue | 25% | 2-D eigenspace; any orthonormal basis is acceptable |
| Negative dominant eigenvalue | 15% | Largest-magnitude eigenvalue is negative |
| Mixed batch | 20% | Three matrices combining the above, in one run |

All five are deterministic and check real numerical behavior (residuals, orthogonality) against independently-computed ground truth, not source inspection.

## Layout

- `instruction.md`: agent request (416 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the power-iteration starter `eigensolve` package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation (cyclic Jacobi eigenvalue algorithm) and installation script.
- `tests/`: runner, grader (independent residual + orthogonality + optimal-matching checks), and fixtures.

## Status

Fully validated end-to-end through real Docker containers: both images build clean; the oracle solution (Jacobi rotations, pure Python) scores `reward=1`, 5/5, on the first run through the real, separate verifier container, converging to machine precision even on the exactly-repeated-eigenvalue case. The power-iteration starter scores `0.55`, correctly failing the clustered-eigenvalue case (and the batch that includes it) via the eigenvector residual check, while passing the well-separated, repeated, and negative-dominant cases where its convergence rate happens to be fast enough. `reproduce.py` reproduces the residual failure live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief, and the QC/QA script once it's provided.
