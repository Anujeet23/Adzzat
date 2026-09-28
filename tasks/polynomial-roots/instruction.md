Replace the real-only Newton's-method solver at `/app/repo/rootfind` with one that reliably finds all roots -- real and complex -- of a real-coefficient polynomial, including clustered, near-degenerate, and exactly repeated roots. Read `/app/TASK_CONTRACT.md` for the exact contract and numerical acceptance criteria before changing anything; `/app/reproduce.py` shows the current implementation failing on a polynomial with no real roots at all.

## Interface

`rootfind.find_roots(coeffs: list[float]) -> list[complex]`, where `coeffs` is real-valued, descending power order (`coeffs[0]` is the `x**n` coefficient). Strip leading zeros before determining the degree `n`; return exactly `n` values, one per root counted with multiplicity, in any order. A degree-0 nonzero constant has no roots (`[]`).

Only the Python standard library is available, in both the agent and verifier images -- no `numpy`, no `scipy`. The difficulty here is genuinely numerical, not a missing library call.

## What "correct" means

Grading constructs each test polynomial from a known, exact set of roots. A submission passes a case only if the returned values, matched optimally one-to-one against the true roots, are each within a stated distance of their match, *and* every returned value has a small residual `|p(r)|` relative to the polynomial's coefficient scale at that magnitude. Collapsing a cluster of close roots onto fewer distinct values, or drifting into values that merely have a small residual without corresponding to a real root, both fail.

## Cases that must work

- Real, well-separated roots.
- Real coefficients with genuinely complex roots (occurring in conjugate pairs), including polynomials with no real roots at all.
- Clustered, nearly-coincident roots (e.g. three real roots within 0.001 of each other) -- naive deflation-based methods accumulate error catastrophically here.
- An exactly repeated root of multiplicity greater than one, where the derivative also vanishes at the root and simple Newton iteration only converges linearly.

## Deliverable

Copy the complete, working `rootfind` package to `/app/submission/rootfind`. The verifier imports only `/app/submission/rootfind` as an unprivileged user in a separate container; it does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria, each checked against a polynomial built from known roots, via optimal matching plus residual: well-separated real roots (15%); real coefficients with complex roots (20%); clustered near-degenerate roots (25%); an exact high-multiplicity root (25%); and a batch of several polynomials combining these cases in one run (15%). A full pass requires all five; per-criterion outcomes are retained separately for diagnosis.
