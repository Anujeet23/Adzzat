"""Square matrix multiplication via the textbook triple loop: correct, but
performs exactly n^3 scalar multiplications, growing 8x every time n
doubles. See /app/TASK_CONTRACT.md.
"""
from . import ops


def matmul(A, B):
    n = len(A)
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            total = 0.0
            for k in range(n):
                total += ops.mul(A[i][k], B[k][j])
            C[i][j] = total
    return C
