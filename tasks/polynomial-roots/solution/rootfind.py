"""Reference implementation: Weierstrass/Durand-Kerner simultaneous iteration.

Unlike sequential Newton + deflation, all n roots are refined together each
iteration, so there is no deflation error to accumulate -- the main reason
naive deflation-based solvers fall apart on clustered or repeated roots.
"""
import cmath


def find_roots(coeffs):
    coeffs = list(coeffs)
    while coeffs and coeffs[0] == 0:
        coeffs = coeffs[1:]
    if not coeffs:
        raise ValueError("zero polynomial has no well-defined roots")
    n = len(coeffs) - 1
    if n == 0:
        return []

    lead = coeffs[0]
    c = [x / lead for x in coeffs]

    def evaluate(z):
        result = 0j
        for coef in c:
            result = result * z + coef
        return result

    cauchy = 1.0 + max(abs(x) for x in c[1:]) if n >= 1 else 1.0
    roots = [
        cauchy * (0.5 + 0.03 * k) * cmath.exp(1j * (2 * cmath.pi * k / n + 0.5))
        for k in range(n)
    ]

    for _ in range(2000):
        max_delta = 0.0
        new_roots = list(roots)
        for i in range(n):
            zi = roots[i]
            denom = 1.0 + 0j
            for j in range(n):
                if j != i:
                    diff = zi - roots[j]
                    if diff == 0:
                        diff = 1e-10 + 1e-10j
                    denom *= diff
            delta = evaluate(zi) / denom
            new_roots[i] = zi - delta
            max_delta = max(max_delta, abs(delta))
        roots = new_roots
        if max_delta < 1e-15:
            break

    return roots
