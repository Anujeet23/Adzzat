"""Reference implementation: Strassen's algorithm. Recursively splits each
n x n matrix (n a power of two) into four (n/2) x (n/2) quadrants and
combines them using 7 recursive multiplications instead of 8, giving
O(n^log2(7)) ~= O(n^2.807) scalar multiplications instead of O(n^3).
Matrix addition/subtraction is not counted -- only ops.mul calls are, since
that is what the harness instruments.
"""
from . import ops


def _add(A, B):
    return [[A[i][j] + B[i][j] for j in range(len(A))] for i in range(len(A))]


def _sub(A, B):
    return [[A[i][j] - B[i][j] for j in range(len(A))] for i in range(len(A))]


def _split(M):
    n = len(M)
    half = n // 2
    A11 = [row[:half] for row in M[:half]]
    A12 = [row[half:] for row in M[:half]]
    A21 = [row[:half] for row in M[half:]]
    A22 = [row[half:] for row in M[half:]]
    return A11, A12, A21, A22


def _combine(C11, C12, C21, C22):
    half = len(C11)
    n = half * 2
    C = [[0.0] * n for _ in range(n)]
    for i in range(half):
        for j in range(half):
            C[i][j] = C11[i][j]
            C[i][j + half] = C12[i][j]
            C[i + half][j] = C21[i][j]
            C[i + half][j + half] = C22[i][j]
    return C


def matmul(A, B):
    n = len(A)
    if n == 1:
        return [[ops.mul(A[0][0], B[0][0])]]

    A11, A12, A21, A22 = _split(A)
    B11, B12, B21, B22 = _split(B)

    M1 = matmul(_add(A11, A22), _add(B11, B22))
    M2 = matmul(_add(A21, A22), B11)
    M3 = matmul(A11, _sub(B12, B22))
    M4 = matmul(A22, _sub(B21, B11))
    M5 = matmul(_add(A11, A12), B22)
    M6 = matmul(_sub(A21, A11), _add(B11, B12))
    M7 = matmul(_sub(A12, A22), _add(B21, B22))

    C11 = _add(_sub(_add(M1, M4), M5), M7)
    C12 = _add(M3, M5)
    C21 = _add(M2, M4)
    C22 = _add(_sub(_add(M1, M3), M2), M6)

    return _combine(C11, C12, C21, C22)
