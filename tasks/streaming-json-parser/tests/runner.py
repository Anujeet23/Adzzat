#!/usr/bin/env python3
"""Feeds a scripted sequence of chunks to the submitted StreamingParser and
checks the exact list of values returned by every single feed() call.
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
        from jsonstream import StreamingParser  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        parser = StreamingParser()
        for step, (chunk, expected) in enumerate(zip(fixture["chunks"], fixture["expected"])):
            got = parser.feed(chunk)
            if got != expected:
                raise AssertionError(
                    "feed(%r) at step %d: expected %r, got %r" % (chunk, step, expected, got)
                )

        result = {"ok": True}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
