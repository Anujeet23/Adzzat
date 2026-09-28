"""Finds polynomial roots via real-valued Newton's method plus synthetic-
division deflation. Works for simple, well-separated real roots, but never
searches the complex plane, and deflation error compounds badly on
clustered or repeated roots. See /app/TASK_CONTRACT.md.
"""


def _eval(poly, x):
    result = 0.0
    for c in poly:
        result = result * x + c
    return result


def _deriv_coeffs(poly):
    n = len(poly) - 1
    return [c * (n - i) for i, c in enumerate(poly[:-1])]


def _deflate(poly, root):
    out = [poly[0]]
    for c in poly[1:-1]:
        out.append(out[-1] * root + c)
    return out


def find_roots(coeffs):
    coeffs = [float(c) for c in coeffs]
    while coeffs and coeffs[0] == 0:
        coeffs = coeffs[1:]
    n = len(coeffs) - 1
    if n <= 0:
        return []

    poly = coeffs[:]
    roots = []
    for _ in range(n):
        x = 1.0
        for _ in range(50):
            value = _eval(poly, x)
            dpoly = _deriv_coeffs(poly)
            deriv = _eval(dpoly, x) if dpoly else 0.0
            if deriv == 0:
                break
            step = value / deriv
            x -= step
            if abs(step) < 1e-12:
                break
        roots.append(complex(x, 0.0))
        poly = _deflate(poly, x)
    return roots
