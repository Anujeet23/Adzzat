"""Demonstrates the current implementation's failure on complex and
clustered roots."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from rootfind import find_roots  # noqa: E402


def poly_eval(coeffs, z):
    result = 0j
    for c in coeffs:
        result = result * z + c
    return result


def main():
    # x^2 + 4 has roots +2i, -2i -- no real root exists at all.
    coeffs = [1.0, 0.0, 4.0]
    roots = find_roots(coeffs)
    residuals = [abs(poly_eval(coeffs, r)) for r in roots]
    print("x^2 + 4, returned roots:", roots)
    print("residuals |p(root)|:", residuals)
    if all(r > 1e-3 for r in residuals):
        print("BUG REPRODUCED: none of the returned values are actually "
              "close to a root -- the search never leaves the real line, "
              "so it cannot find this polynomial's purely imaginary roots.")


if __name__ == "__main__":
    main()
