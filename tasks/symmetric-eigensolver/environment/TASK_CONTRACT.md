# Symmetric eigensolver — contract

Source: an original, minimal starter at `/app/repo/eigensolve`, not a fork of an existing project.

## API

```python
def eigh(matrix: list[list[float]]) -> tuple[list[float], list[list[float]]]:
    ...
```

`matrix` is a real, symmetric, `n x n` matrix (given as a list of `n` rows, each a list of `n` floats; `matrix[i][j] == matrix[j][i]` for all valid tests). Returns `(eigenvalues, eigenvectors)`: `eigenvalues` is a list of `n` real numbers (with multiplicity), and `eigenvectors[j]` is the unit-norm eigenvector corresponding to `eigenvalues[j]`, i.e. `eigenvectors` is a list of `n` vectors each of length `n`. Order is unspecified but must be consistent between the two returned lists (the `j`-th eigenvector must actually correspond to the `j`-th eigenvalue).

## Environment constraint

Only the Python standard library is available, in both the agent and verifier images -- no `numpy`, no `scipy`. The difficulty is in implementing the numerics correctly, not in wiring up an existing linear-algebra routine.

## What "correct" means

Grading constructs each test matrix from a known, exact set of eigenvalues and a known orthonormal eigenvector basis. It checks, independently of anything the submission claims:

1. The returned eigenvalues, matched optimally one-to-one against the true eigenvalues, are each within a stated tolerance.
2. For every `j`, `eigenvectors[j]` is unit norm and satisfies `A @ eigenvectors[j] ≈ eigenvalues[j] * eigenvectors[j]` (the residual, evaluated by the grader's own matrix-vector product, not the submission's).
3. The full set of returned eigenvectors is mutually orthogonal (`V^T V ≈ I`).

Eigenvector *direction* is intentionally not checked against the reference basis when an eigenvalue has multiplicity greater than one: any orthonormal basis of that eigenspace is valid, and the residual + orthogonality checks above are sufficient to verify correctness without over-constraining an inherently non-unique choice.

## What's out of scope

Non-symmetric matrices, matrices larger than 6x6, and complex-valued input. Runtime is not directly graded, but each verification call is bounded to a generous but finite wall-clock limit.

## Delivery

Copy the complete `eigensolve` package to `/app/submission/eigensolve`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
