#!/usr/bin/env python3
"""Runs the submitted transpose(n) on a deterministic n x n matrix, using
the submission's own kernel.mem simulated cache to collect miss stats, and
reports the resulting array plus the miss count as JSON. Correctness
checking against an independent reference happens in grade.py.
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
        from kernel import mem  # noqa: E402
        from kernel import transpose  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)
        n = fixture["n"]

        mem.set_array(0, [float(i) for i in range(n * n)])
        mem.set_array(1, [0.0] * (n * n))
        mem.reset()
        transpose(n)
        stats = mem.stats()
        out_array = mem.get_array(1)

        result = {"ok": True, "out": out_array, "misses": stats["misses"], "accesses": stats["accesses"]}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
