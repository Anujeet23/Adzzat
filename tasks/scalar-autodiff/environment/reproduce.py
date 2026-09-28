"""Demonstrates the current engine's gradient-accumulation bug: it computes
correct gradients when every Value is used once, but silently drops
contributions when a Value feeds into more than one downstream operation.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from autodiff import Value  # noqa: E402


def main():
    # y = x^2 + x^3, where x is used by two separate multiplications that
    # both flow back into x. dy/dx = 2x + 3x^2.
    x = Value(2.0)
    t = x * x
    u = x * t
    y = t + u
    y.backward()

    analytic = 2 * x.data + 3 * x.data ** 2
    print("x =", x.data, " y = x^2 + x^3 =", y.data)
    print("true dy/dx =", analytic)
    print("engine's x.grad =", x.grad)
    if abs(x.grad - analytic) > 1e-6:
        print("BUG REPRODUCED: x.grad only reflects the last edge that "
              "wrote to it, not the sum over every path from x to y.")


if __name__ == "__main__":
    main()
