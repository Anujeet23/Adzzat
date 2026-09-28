#!/usr/bin/env python3
"""Calls the submitted find_roots() on one or more polynomials and reports
the raw results as JSON. All numerical acceptance checking (matching against
known true roots, residual tolerances) happens in grade.py, in the grader's
own process, using its own independent polynomial evaluator -- the runner
never trusts anything the submission computes beyond the returned root list.
"""
import argparse
import json
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkgdir", required=True)
    ap.add_argument("--ops", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    result = {"ok": False}
    try:
        sys.path.insert(0, args.pkgdir)
        from rootfind import find_roots  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        if "polynomials" in fixture:
            polys = fixture["polynomials"]
        else:
            polys = [{"coeffs": fixture["coeffs"]}]

        outputs = []
        for entry in polys:
            started = time.monotonic()
            roots = find_roots(list(entry["coeffs"]))
            elapsed = time.monotonic() - started
            pairs = [[float(r.real), float(r.imag)] for r in roots]
            outputs.append({"roots": pairs, "seconds": elapsed})

        result = {"ok": True, "results": outputs}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
