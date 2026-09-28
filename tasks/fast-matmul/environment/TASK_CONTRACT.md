# Fast matrix multiplication — contract

Source: an original, minimal starter at `/app/repo/kernel`, not a fork of an existing project.

## API

```python
def matmul(A: list[list[float]], B: list[list[float]]) -> list[list[float]]:
    ...
```

`A` and `B` are square `n x n` matrices (lists of `n` lists of `n` floats), where `n` is always a power of two in graded inputs. Returns their `n x n` matrix product.

## The instrumentation requirement

Every scalar multiplication your implementation performs, at any level of recursion, must be performed by calling `kernel.ops.mul(a, b)` through the module reference (`from . import ops; ops.mul(a, b)`), never `from .ops import mul` and never Python's `*` operator directly on two scalars. The grading harness replaces the `mul` attribute on the `ops` module with an instrumented wrapper that counts calls; multiplications performed any other way are invisible to it and cannot count toward reducing your total. `ops.mul(a, b)` always returns `a * b` -- wrapping it changes nothing about the arithmetic, only what the harness can observe.

Elementwise matrix addition/subtraction is not counted and is not restricted.

## What's graded

1. **Correctness.** The returned matrix must match the true product to a small floating-point tolerance, checked by the grader's own independently computed reference, for several matrix sizes.
2. **Asymptotic multiplication count.** As `n` doubles, the number of `ops.mul` calls must grow by meaningfully less than the 8x that an `O(n^3)` algorithm (e.g. the textbook triple loop) always shows -- this is checked as a ratio between consecutive doubled sizes, not a fixed absolute number, so it does not depend on any particular constant-factor implementation detail.

## What's out of scope

Matrix sizes that are not a power of two, non-square matrices, complex numbers, and parallelism -- this is a single-threaded, single-process algorithmic problem.

## Delivery

Copy the complete `kernel` package (including `ops.py`, whether or not you changed it) to `/app/submission/kernel`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
