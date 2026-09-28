Replace the power-iteration-plus-deflation eigensolver at `/app/repo/eigensolve` with one that reliably finds all eigenvalues and an orthonormal eigenvector basis of a real symmetric matrix, including when eigenvalues are closely clustered or exactly repeated. Read `/app/TASK_CONTRACT.md` for the exact contract and numerical acceptance criteria before changing anything; `/app/reproduce.py` shows the current implementation failing to separate two eigenvalues 0.001 apart.

## Interface

`eigensolve.eigh(matrix: list[list[float]]) -> tuple[list[float], list[list[float]]]`. `matrix` is real, symmetric, `n x n`. Return `(eigenvalues, eigenvectors)` where `eigenvectors[j]` is the unit-norm eigenvector for `eigenvalues[j]` -- the two lists must stay correctly paired by index, but their overall order is unspecified.

Only the Python standard library is available, in both the agent and verifier images -- no `numpy`, no `scipy`. The difficulty here is genuinely numerical, not a missing library call.

## What "correct" means

Grading constructs each test matrix from a known, exact set of eigenvalues and a known orthonormal basis, but never trusts the submission's own claims: it independently checks that the returned eigenvalues, matched optimally against the true ones, are each within tolerance; that each `eigenvectors[j]` is unit norm and satisfies `A @ eigenvectors[j] ≈ eigenvalues[j] * eigenvectors[j]` under the grader's own matrix-vector product; and that the full returned eigenvector set is mutually orthogonal. Eigenvector *direction* is intentionally not checked against the reference basis when an eigenvalue is repeated, since any orthonormal basis of that eigenspace is valid -- the residual and orthogonality checks are what actually matter there.

## Cases that must work

- Well-separated eigenvalues.
- Two eigenvalues clustered within 0.001 of each other -- power iteration's convergence rate depends on the ratio between the top two eigenvalue magnitudes, so it stalls badly here.
- An exactly repeated eigenvalue, where the corresponding eigenspace is two-dimensional and any orthonormal basis of it is an acceptable answer.
- A matrix whose eigenvalue of largest magnitude is negative.

## Deliverable

Copy the complete, working `eigensolve` package to `/app/submission/eigensolve`. The verifier imports only `/app/submission/eigensolve` as an unprivileged user in a separate container; it does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria, each checked against a matrix built from a known eigendecomposition, via optimal eigenvalue matching plus independent residual and orthogonality checks: well-separated eigenvalues (15%); clustered eigenvalues 0.001 apart (25%); an exactly repeated eigenvalue (25%); a matrix with a negative dominant eigenvalue (15%); and a batch of several matrices combining these cases in one run (20%). A full pass requires all five; per-criterion outcomes are retained separately for diagnosis.
