# Robust polynomial root finder — contract

Source: an original, minimal starter at `/app/repo/rootfind`, not a fork of an existing project.

## API

```python
def find_roots(coeffs: list[float]) -> list[complex]:
    ...
```

`coeffs` is a list of real numbers in descending power order: `coeffs[0]` is the coefficient of `x**n`, `coeffs[-1]` is the constant term. Leading zero coefficients may be present and must be stripped before determining the degree. The input polynomial always has real coefficients, but its roots may be complex; complex roots of a real polynomial occur in conjugate pairs. Return exactly one entry per root, counted with multiplicity, in any order -- so for a degree-`n` polynomial (after stripping leading zeros), the returned list has length `n`. A degree-0 (constant, nonzero) polynomial has no roots; return `[]`. The all-zero polynomial has no well-defined roots; you may raise any exception for it (not graded).

## Environment constraint

Only the Python standard library is available, in both the agent and verifier images -- no `numpy`, no `scipy`. This is deliberate: the difficulty is in the numerics, not in wiring up an existing linear-algebra routine.

## What "correct" means

A returned value `r` is an acceptable root if `|p(r)|` is small relative to the polynomial's coefficient scale at `|r|` -- not exact equality, since floating point roots (especially clustered or repeated ones) cannot be found to arbitrary precision. Grading constructs each test polynomial from a known, exact set of roots and checks two things independently: the residual `|p(r)|` for every returned value, and that the returned values, matched optimally one-to-one against the true roots, are each within a stated distance of their match. Both checks must pass; a solution that returns values with a tiny residual but that don't correspond to the actual distinct roots (e.g. collapsing a cluster of 3 close roots onto 1 repeated 3 times) fails the matching check even though the residual check alone might not catch it.

## What's out of scope

Polynomials of degree above 10, complex input coefficients, and numerical precision beyond standard IEEE double (`float`/`complex`). Runtime is not directly graded, but each verification call is bounded to a generous but finite wall-clock limit.

## Delivery

Copy the complete `rootfind` package to `/app/submission/rootfind`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
