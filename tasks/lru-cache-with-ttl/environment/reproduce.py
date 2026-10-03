"""Demonstrates a stale read and an incorrect eviction with the current
implementation, using a fake clock so this is fully deterministic."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from cache import TTLCache  # noqa: E402


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, by):
        self.t += by


def main():
    clock = FakeClock()
    cache = TTLCache(max_size=5, clock=clock)
    cache.put("session", "token-abc", ttl=10)
    clock.advance(15)
    try:
        value = cache.get("session")
        print("BUG REPRODUCED: get('session') returned %r, 5 ticks after its "
              "ttl=10 expired -- a stale read." % value)
    except KeyError:
        print("get('session') correctly raised KeyError")

    print()
    clock2 = FakeClock()
    cache2 = TTLCache(max_size=2, clock=clock2)
    cache2.put("a", "va", ttl=1000)
    cache2.put("b", "vb", ttl=1000)
    cache2.get("a")  # touch a -- a should now be the least likely to be evicted
    cache2.put("c", "vc", ttl=1000)  # cache full; must evict the untouched key, b
    try:
        value = cache2.get("a")
        print("get('a') correctly survived eviction:", value)
    except KeyError:
        print("BUG REPRODUCED: 'a' was evicted even though it was the most "
              "recently *read* key -- get() never refreshes recency, only "
              "put() does.")


if __name__ == "__main__":
    main()
