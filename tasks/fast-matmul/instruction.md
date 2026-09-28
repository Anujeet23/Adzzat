Replace the textbook triple-loop matrix multiplication at `/app/repo/kernel` with an algorithm that performs asymptotically fewer scalar multiplications -- not just fewer wall-clock seconds -- while remaining correct. Read `/app/TASK_CONTRACT.md` for the exact instrumentation requirement before changing anything; `/app/reproduce.py` shows the current implementation's multiplication count growing exactly 8x every time the matrix size doubles.

## Interface

`kernel.matmul(A, B)` multiplies two `n x n` matrices (lists of `n` lists of `n` floats), where `n` is always a power of two. Every scalar multiplication anywhere in your implementation, at any recursion depth, must be performed by calling `kernel.ops.mul(a, b)` through the module reference (`from . import ops; ops.mul(a, b)`), not `from .ops import mul` and not Python's `*` operator directly on two scalars -- the grading harness instruments exactly that one attribute to count how many scalar multiplications your algorithm actually performs. `ops.mul` computes the real product; wrapping it changes nothing about correctness, only what the harness can observe. Matrix addition/subtraction is unrestricted and uncounted.

## What's graded

Correctness (the result must match the true product to a small tolerance, checked independently), and the asymptotic growth of the multiplication count: as `n` doubles, the count must grow by meaningfully less than the 8x that any `O(n^3)` algorithm always shows, checked as a ratio between doubled sizes rather than a fixed absolute number -- so it does not depend on constant-factor implementation details, only on genuinely reducing the number of multiplications through recursive decomposition.

## Deliverable

Copy the complete, working `kernel` package (including `ops.py`, whether or not you changed it) to `/app/submission/kernel`. The verifier imports only `/app/submission/kernel` as an unprivileged user in a separate container; it does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria: correctness at a small size (20%); correctness at a larger size (15%); multiplication-count growth ratio staying meaningfully below 8x when size doubles from 16 to 32 (25%); the same ratio check doubling from 32 to 64 (25%); and an absolute sanity bound on the multiplication count at size 16, closing the loophole of gaming the ratio checks alone (15%). A full pass requires all five; per-criterion outcomes are retained separately for diagnosis.

Only the Python standard library is available at verification time; no network access.
