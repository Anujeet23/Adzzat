"""Demonstrates the current implementation's cache-miss count exploding
once the matrix no longer fits in the simulated cache."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from kernel import mem  # noqa: E402
from kernel import transpose  # noqa: E402


def measure(n):
    mem.set_array(0, [float(i) for i in range(n * n)])
    mem.set_array(1, [0.0] * (n * n))
    mem.reset()
    transpose(n)
    return mem.stats()["misses"]


def main():
    m32 = measure(32)
    m64 = measure(64)
    print("cache misses at n=32:", m32)
    print("cache misses at n=64:", m64)
    print("ratio:", m64 / m32)
    if m64 / m32 > 6.0:
        print("BUG REPRODUCED: quadrupling the data (doubling n) more than "
              "sextuples the miss count -- the matrix has outgrown the "
              "simulated cache and the column-major write pattern is "
              "thrashing it on every row.")


if __name__ == "__main__":
    main()
