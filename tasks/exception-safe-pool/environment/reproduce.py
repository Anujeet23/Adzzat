"""Demonstrates the current implementation's capacity leaks."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from pool import ResourcePool, PoolExhausted  # noqa: E402


def factory_fails_once():
    calls = {"n": 0}

    def factory():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated: downstream service unavailable")
        return object()

    return factory


def main():
    pool = ResourcePool(factory=factory_fails_once(), max_size=1)
    try:
        pool.acquire()
    except RuntimeError:
        print("factory failed on first attempt, as expected")

    try:
        h = pool.acquire()
        print("second acquire succeeded:", h.resource)
    except PoolExhausted:
        print("BUG REPRODUCED: pool reports exhausted after a single factory "
              "failure, even though max_size=1 and nothing has ever been "
              "successfully checked out yet.")

    print()
    pool2 = ResourcePool(factory=lambda: object(), max_size=1)
    try:
        with pool2.acquire() as h:
            raise ValueError("caller code failed for an unrelated reason")
    except ValueError:
        pass
    try:
        pool2.acquire()
        print("pool2: second acquire succeeded, resource was returned correctly")
    except PoolExhausted:
        print("BUG REPRODUCED: an exception in caller code, unrelated to the "
              "resource itself, permanently leaked the resource -- the pool "
              "never sees it again.")


if __name__ == "__main__":
    main()
