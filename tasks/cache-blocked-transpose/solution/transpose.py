"""Reference implementation: tile the n x n matrix into TILE x TILE blocks
(TILE chosen to match the simulated cache's line size) and fully transpose
each block before moving to the next. Every line touched by a block stays
resident for that block's entire, small amount of work, instead of being
evicted and reloaded on every row as the naive row-major/column-major
mismatch does.
"""
from . import mem

TILE = 8


def transpose(n):
    for block_i in range(0, n, TILE):
        for block_j in range(0, n, TILE):
            i_end = min(block_i + TILE, n)
            j_end = min(block_j + TILE, n)
            for i in range(block_i, i_end):
                for j in range(block_j, j_end):
                    value = mem.read(0, i * n + j)
                    mem.write(1, j * n + i, value)
