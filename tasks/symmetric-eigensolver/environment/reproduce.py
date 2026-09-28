"""Demonstrates the current implementation failing to separate two close
eigenvalues within a practical iteration budget."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from eigensolve import eigh  # noqa: E402


def main():
    # Symmetric matrix with true eigenvalues 3.0 and 3.001 (plus -1.0);
    # power iteration's convergence rate depends on their ratio (~1.0003),
    # so 200 iterations is nowhere near enough to tell them apart.
    matrix = [
        [2.9180273283, 0.1345571444, 0.5506124285],
        [0.1345571444, 2.7795908139, -0.9047530713],
        [0.5506124285, -0.9047530713, -0.6966181422],
    ]
    true_eigenvalues = [3.0, 3.001, -1.0]
    values, vectors = eigh(matrix)
    print("true eigenvalues:  ", true_eigenvalues)
    print("returned eigenvalues:", values)

    n = len(matrix)
    worst = 0.0
    for lam, v in zip(values, vectors):
        Av = [sum(matrix[i][k] * v[k] for k in range(n)) for i in range(n)]
        residual = max(abs(Av[i] - lam * v[i]) for i in range(n))
        worst = max(worst, residual)
    print("worst |A v - lambda v| residual across returned eigenpairs:", worst)
    if worst > 1e-6:
        print("BUG REPRODUCED: an eigenpair fails the basic A v = lambda v "
              "equation by a wide margin -- power iteration hasn't converged "
              "for the clustered pair, so deflation carries that error into "
              "an eigenvector that doesn't actually belong to its reported "
              "eigenvalue.")


if __name__ == "__main__":
    main()
