# Cache-blocked transpose — contract

Source: an original, minimal starter at `/app/repo/kernel`, not a fork of an existing project.

## API

```python
def transpose(n: int) -> None:
    ...
```

Transposes the `n x n` matrix held in simulated array `0` (row-major: element `(row, col)` is at index `row * n + col`) into simulated array `1`, in place from the caller's point of view (array `1` is pre-sized and zeroed before `transpose` is called). `n` is always a positive multiple of 8 in graded inputs.

## The instrumentation requirement

Every element read or write your implementation performs must go through `kernel.mem.read(array_id, index)` / `kernel.mem.write(array_id, index, value)`, called via the module reference (`from . import mem; mem.read(...)`), never `from .mem import read`. The grading harness simulates a small, fixed-capacity cache behind these two functions: addresses within each array are grouped into fixed-size lines (`mem.BLOCK_SIZE` consecutive elements per line), and touching a line that isn't currently resident is a miss that evicts the least-recently-used resident line once the cache (`mem.NUM_LINES` lines total, shared across both arrays) is full. Accesses performed any other way -- indexing a plain Python list directly, for instance -- are invisible to this simulation.

`mem.set_array`, `mem.get_array`, and `mem.reset` are grading-support functions for setting up input and reading back output; they bypass the simulated cache and are not for use inside `transpose` itself.

## What's graded

1. **Correctness.** After `transpose(n)`, array 1 must equal the true transpose of array 0, checked exactly.
2. **Cache-miss count.** For an `n` large enough that the matrix no longer fits in the simulated cache, a naive access pattern (e.g. reading array 0 row-major while writing array 1 at a stride of `n`) causes the destination's cache lines to be evicted and reloaded on almost every row -- far more misses than the `O(n^2 / BLOCK_SIZE)` that is achievable, and than the total amount of data actually requires. Grading checks both the growth in miss count as `n` doubles, and absolute miss-count bounds at two sizes.

## What's out of scope

Matrix sizes that aren't a multiple of 8, non-square matrices, and any real hardware profiling -- everything happens inside the simulated cache above.

## Delivery

Copy the complete `kernel` package (including `mem.py`, whether or not you changed it) to `/app/submission/kernel`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
