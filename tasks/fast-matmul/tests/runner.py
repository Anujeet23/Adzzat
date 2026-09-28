#!/usr/bin/env python3
"""Runs the submitted matmul() on a fixture matrix pair, counting calls to
kernel.ops.mul, and reports the result matrix plus the call count as JSON.
Correctness checking against an independent reference happens in grade.py.
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
        import kernel.ops as ops_mod  # noqa: E402
        from kernel import matmul  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        original = ops_mod.mul
        count = [0]

        def counted(a, b):
            count[0] += 1
            return original(a, b)

        ops_mod.mul = counted
        try:
            C = matmul(fixture["A"], fixture["B"])
        finally:
            ops_mod.mul = original

        result = {"ok": True, "C": C, "mul_count": count[0]}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
