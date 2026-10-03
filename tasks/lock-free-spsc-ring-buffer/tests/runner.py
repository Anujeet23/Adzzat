#!/usr/bin/env python3
"""Executes a scripted sequence of push/pop/len operations against the
submitted RingBuffer and checks every op's expected outcome.
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkgdir", required=True)
    ap.add_argument("--ops", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    result = {"ok": False}
    try:
        sys.path.insert(0, args.pkgdir)
        from ringbuffer import RingBuffer, Empty  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        rb = RingBuffer(capacity=fixture["capacity"])

        for step, op in enumerate(fixture["ops"]):
            kind = op["op"]

            if kind == "push":
                got = rb.push(op["item"])
                if got != op["expect"]:
                    raise AssertionError(
                        "push(%r) at step %d: expected %s, got %s" % (op["item"], step, op["expect"], got)
                    )

            elif kind == "pop":
                if op["expect"] == "empty":
                    try:
                        rb.pop()
                    except Empty:
                        pass
                    else:
                        raise AssertionError("expected Empty at step %d, got a value" % step)
                else:
                    try:
                        got = rb.pop()
                    except Empty:
                        raise AssertionError("expected pop()=%r at step %d, got Empty" % (op["value"], step))
                    if got != op["value"]:
                        raise AssertionError(
                            "expected pop()=%r at step %d, got %r" % (op["value"], step, got)
                        )

            elif kind == "expect_len":
                actual = len(rb)
                if actual != op["value"]:
                    raise AssertionError("expected len=%d at step %d, got %d" % (op["value"], step, actual))

            else:
                raise ValueError("unknown op: " + kind)

        result = {"ok": True, "final_len": len(rb)}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
