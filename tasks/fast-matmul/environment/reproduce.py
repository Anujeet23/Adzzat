"""Demonstrates the current implementation's multiplication count growing
8x every time the matrix size doubles -- exactly the textbook O(n^3)
signature, not a sub-cubic one."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
import kernel.ops as ops_mod  # noqa: E402
from kernel import matmul  # noqa: E402


def count_mults(n):
    original = ops_mod.mul
    count = [0]

    def counted(a, b):
        count[0] += 1
        return original(a, b)

    ops_mod.mul = counted
    try:
        A = [[float(i + j) for j in range(n)] for i in range(n)]
        B = [[float(i - j) for j in range(n)] for i in range(n)]
        matmul(A, B)
    finally:
        ops_mod.mul = original
    return count[0]


def main():
    c16 = count_mults(16)
    c32 = count_mults(32)
    ratio = c32 / c16
    print("multiplications at n=16:", c16)
    print("multiplications at n=32:", c32)
    print("ratio (should be well under 8.0 for a sub-cubic algorithm):", ratio)
    if ratio > 7.5:
        print("BUG REPRODUCED: doubling n multiplies the scalar-multiplication "
              "count by roughly 8x, the signature of an O(n^3) algorithm.")


if __name__ == "__main__":
    main()
