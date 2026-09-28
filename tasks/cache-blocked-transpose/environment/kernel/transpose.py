"""Transposes the n x n matrix in array 0 into array 1, row by row. Reads
of array 0 are sequential and cache-friendly, but each row's elements are
written to array 1 at stride n apart -- for any n larger than the
simulated cache can hold, this write pattern evicts and reloads the same
destination cache lines over and over. See /app/TASK_CONTRACT.md.
"""
from . import mem


def transpose(n):
    for i in range(n):
        for j in range(n):
            value = mem.read(0, i * n + j)
            mem.write(1, j * n + i, value)
