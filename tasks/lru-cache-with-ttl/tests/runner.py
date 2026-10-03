#!/usr/bin/env python3
"""Executes a scripted sequence of cache operations against the submitted
TTLCache, driven by a fake, caller-controlled clock so nothing about real
elapsed time is ever involved, and checking every op's expected outcome.
"""
import argparse
import json
import sys


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, by):
        self.t += by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkgdir", required=True)
    ap.add_argument("--ops", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    result = {"ok": False}
    try:
        sys.path.insert(0, args.pkgdir)
        from cache import TTLCache  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        clock = FakeClock()
        cache = TTLCache(max_size=fixture["max_size"], clock=clock)

        for step, op in enumerate(fixture["ops"]):
            kind = op["op"]

            if kind == "put":
                cache.put(op["key"], op["value"], op["ttl"])

            elif kind == "get_hit":
                try:
                    got = cache.get(op["key"])
                except KeyError:
                    raise AssertionError(
                        "expected a hit for key %r at step %d, got a miss" % (op["key"], step)
                    )
                if got != op["value"]:
                    raise AssertionError(
                        "key %r at step %d: expected %r, got %r" % (op["key"], step, op["value"], got)
                    )

            elif kind == "get_miss":
                try:
                    cache.get(op["key"])
                except KeyError:
                    pass
                else:
                    raise AssertionError("expected a miss for key %r at step %d, got a hit" % (op["key"], step))

            elif kind == "advance":
                clock.advance(op["by"])

            elif kind == "expect_len":
                actual = len(cache)
                if actual != op["value"]:
                    raise AssertionError("expected len=%d at step %d, got %d" % (op["value"], step, actual))

            else:
                raise ValueError("unknown op: " + kind)

        result = {"ok": True, "final_len": len(cache)}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
