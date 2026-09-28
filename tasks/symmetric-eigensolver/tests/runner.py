#!/usr/bin/env python3
"""Calls the submitted eigh() on one or more matrices and reports the raw
results as JSON. All numerical acceptance checking happens in grade.py, in
the grader's own process, using an independently computed matrix-vector
product -- the runner never trusts anything the submission computes beyond
the returned eigenvalues/eigenvectors.
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
        from eigensolve import eigh  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        if "matrices" in fixture:
            entries = fixture["matrices"]
        else:
            entries = [fixture]

        outputs = []
        for entry in entries:
            started = time.monotonic()
            values, vectors = eigh([list(row) for row in entry["matrix"]])
            elapsed = time.monotonic() - started
            outputs.append(
                {
                    "eigenvalues": [float(v) for v in values],
                    "eigenvectors": [[float(x) for x in vec] for vec in vectors],
                    "seconds": elapsed,
                }
            )

        result = {"ok": True, "results": outputs}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
