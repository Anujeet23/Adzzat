#!/usr/bin/env python3
"""Executes a scripted sequence of token-bucket operations against the
submitted TokenBucket, driven by a fake, caller-controlled clock, checking
every op's expected outcome (booleans exactly, token counts within a
small float tolerance).
"""
import argparse
import json
import sys

TOLERANCE = 1e-6


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
        from ratelimit import TokenBucket  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        clock = FakeClock()
        bucket = TokenBucket(
            capacity=fixture["capacity"], refill_rate=fixture["refill_rate"], clock=clock
        )

        for step, op in enumerate(fixture["ops"]):
            kind = op["op"]

            if kind == "try_acquire":
                got = bucket.try_acquire(cost=op["cost"])
                if got != op["expect"]:
                    raise AssertionError(
                        "try_acquire(cost=%s) at step %d: expected %s, got %s"
                        % (op["cost"], step, op["expect"], got)
                    )

            elif kind == "advance":
                clock.advance(op["by"])

            elif kind == "expect_available":
                actual = bucket.available()
                if abs(actual - op["value"]) > TOLERANCE:
                    raise AssertionError(
                        "expected available()=%s at step %d, got %s" % (op["value"], step, actual)
                    )

            else:
                raise ValueError("unknown op: " + kind)

        result = {"ok": True, "final_available": bucket.available()}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
