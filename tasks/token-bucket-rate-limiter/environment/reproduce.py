"""Demonstrates the unbounded-burst and lost-fractional-refill bugs, using
a fake clock so this is fully deterministic."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from ratelimit import TokenBucket  # noqa: E402


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, by):
        self.t += by


def main():
    clock = FakeClock()
    bucket = TokenBucket(capacity=5, refill_rate=1, clock=clock)
    bucket.try_acquire(cost=5)  # drain to 0
    clock.advance(100)  # idle for a long time
    available = bucket.available()
    if available > 5:
        print("BUG REPRODUCED: available()=%s after a long idle period, "
              "exceeding capacity=5 -- refill never clamps." % available)
    else:
        print("available() correctly clamped at", available)

    print()
    clock2 = FakeClock()
    bucket2 = TokenBucket(capacity=100, refill_rate=1, clock=clock2)
    bucket2.try_acquire(cost=100)  # drain to 0
    for _ in range(5):
        clock2.advance(0.9)
        bucket2.available()
    expected = 4.5
    actual = bucket2.available()
    if abs(actual - expected) > 1e-6:
        print("BUG REPRODUCED: after five advances of 0.9 clock units each "
              "(4.5 total), available()=%s instead of %s -- fractional "
              "refill time is being silently dropped." % (actual, expected))
    else:
        print("available() correctly credited the full elapsed time:", actual)


if __name__ == "__main__":
    main()
