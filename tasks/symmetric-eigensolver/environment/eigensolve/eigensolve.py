"""Finds eigenvalues/eigenvectors of a real symmetric matrix via power
iteration on the largest-magnitude eigenvalue, then rank-1 deflation for
the rest. Convergence rate depends on the ratio between the two largest
eigenvalue magnitudes, so this fails badly when eigenvalues are clustered
close together. See /app/TASK_CONTRACT.md.
"""


def _matvec(A, v):
    n = len(A)
    return [sum(A[i][k] * v[k] for k in range(n)) for i in range(n)]


def eigh(matrix):
    n = len(matrix)
    A = [list(row) for row in matrix]
    eigenvalues = []
    eigenvectors = []

    for _ in range(n):
        v = [1.0] * n
        lam = 0.0
        for _ in range(200):
            Av = _matvec(A, v)
            norm = sum(x * x for x in Av) ** 0.5
            if norm == 0:
                break
            v = [x / norm for x in Av]
            lam = sum(vi * awi for vi, awi in zip(v, _matvec(A, v)))
        eigenvalues.append(lam)
        eigenvectors.append(v)
        for i in range(n):
            for j in range(n):
                A[i][j] -= lam * v[i] * v[j]

    return eigenvalues, eigenvectors
