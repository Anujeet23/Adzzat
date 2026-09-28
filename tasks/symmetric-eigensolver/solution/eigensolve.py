"""Reference implementation: the classical cyclic Jacobi eigenvalue
algorithm for real symmetric matrices. Each sweep zeroes one off-diagonal
pair via a Givens rotation; the accumulated product of rotations is an
orthogonal matrix whose columns are the eigenvectors, which is why this
method never needs deflation and stays numerically well-behaved even for
clustered or exactly repeated eigenvalues.
"""
import math


def eigh(matrix):
    n = len(matrix)
    A = [list(row) for row in matrix]
    V = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    def off_diagonal_norm():
        total = 0.0
        for i in range(n):
            for j in range(n):
                if i != j:
                    total += A[i][j] * A[i][j]
        return total ** 0.5

    for _ in range(200):
        if off_diagonal_norm() < 1e-14:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                apq = A[p][q]
                if abs(apq) < 1e-300:
                    continue
                theta = (A[q][q] - A[p][p]) / (2.0 * apq)
                sign = 1.0 if theta >= 0 else -1.0
                t = sign / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c

                app, aqq = A[p][p], A[q][q]
                A[p][p] = c * c * app - 2.0 * s * c * apq + s * s * aqq
                A[q][q] = s * s * app + 2.0 * s * c * apq + c * c * aqq
                A[p][q] = 0.0
                A[q][p] = 0.0

                for i in range(n):
                    if i != p and i != q:
                        aip, aiq = A[i][p], A[i][q]
                        A[i][p] = c * aip - s * aiq
                        A[p][i] = A[i][p]
                        A[i][q] = s * aip + c * aiq
                        A[q][i] = A[i][q]

                for i in range(n):
                    vip, viq = V[i][p], V[i][q]
                    V[i][p] = c * vip - s * viq
                    V[i][q] = s * vip + c * viq

    eigenvalues = [A[i][i] for i in range(n)]
    eigenvectors = [[V[i][j] for i in range(n)] for j in range(n)]
    return eigenvalues, eigenvectors
