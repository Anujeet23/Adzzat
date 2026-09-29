Replace the row-major/column-major mismatched matrix transpose at `/app/repo/kernel` with a cache-blocked (tiled) one that keeps the simulated cache-miss count close to the theoretical minimum, not thrashing on every row once the matrix outgrows the cache. Read `/app/TASK_CONTRACT.md` for the exact instrumentation requirement before changing anything; `/app/reproduce.py` shows the miss count exploding once `n` crosses that point.

## Interface

`kernel.transpose(n)` transposes the `n x n` matrix in simulated array `0` (row-major) into simulated array `1`; `n` is always a positive multiple of 8. Every element access must go through `kernel.mem.read(array_id, index)` / `kernel.mem.write(array_id, index, value)`, called via the module reference (`from . import mem; mem.read(...)`), not `from .mem import read` -- the grading harness simulates a small, fixed-capacity LRU cache behind exactly these two functions, grouping addresses into `mem.BLOCK_SIZE`-element lines across `mem.NUM_LINES` total resident lines shared by both arrays. Accesses performed any other way are invisible to the simulation. `mem.set_array`/`mem.get_array`/`mem.reset` are grading-support functions, not for use inside `transpose`. `kernel/mem.py` is graded infrastructure -- whatever you submit there is ignored and replaced with the verifier's own trusted copy.

## What's graded

Correctness -- array 1 must equal the true transpose of array 0, checked exactly. And the simulated cache-miss count: once the matrix outgrows the cache, reading array 0 row-major while writing array 1 at a stride of `n` evicts and reloads the same destination lines on almost every row, giving far more misses than the achievable `O(n^2 / BLOCK_SIZE)`. Grading checks both the growth in miss count as `n` doubles and absolute miss-count bounds at two sizes large enough to exceed cache capacity.

## Deliverable

Copy the complete, working `kernel` package (including `mem.py`, whether or not you changed it) to `/app/submission/kernel`. The verifier imports only `/app/submission/kernel` as an unprivileged user in a separate container; it does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria: correctness at a small size that fits entirely in the cache (20%); correctness at a size that doesn't (15%); miss-count growth ratio staying meaningfully below 6x when size doubles from 32 to 64 (25%); an absolute miss-count bound at n=64 (25%); and an absolute miss-count bound at n=128 (15%). A full pass requires all five; per-criterion outcomes are retained separately for diagnosis.

Only the Python standard library is available at verification time; no network access.
