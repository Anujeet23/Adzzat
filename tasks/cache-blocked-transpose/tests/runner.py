#!/usr/bin/env python3
"""Runs the submitted transpose(n) on a deterministic n x n matrix, using
this grader's own trusted kernel.mem simulated cache (substituted over
whatever the submission provided at that path) to collect miss stats, and
reports the resulting array plus the miss count as JSON. Correctness
checking against an independent reference happens in grade.py.

Before importing, the submission's kernel package is copied to a writable
staging directory and its kernel/mem.py is replaced with this grader's own
trusted copy (mem_trusted.py, next to this file), so a submission cannot
report its own, more favorable hit/miss counts; only kernel/transpose.py
is graded.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile


def prepare_pkgdir(orig_pkgdir):
    staged = tempfile.mkdtemp(prefix="kernel-stage-")
    shutil.copytree(os.path.join(orig_pkgdir, "kernel"), os.path.join(staged, "kernel"))
    trusted_mem = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mem_trusted.py")
    shutil.copyfile(trusted_mem, os.path.join(staged, "kernel", "mem.py"))
    return staged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkgdir", required=True)
    ap.add_argument("--ops", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    result = {"ok": False}
    try:
        staged = prepare_pkgdir(args.pkgdir)
        sys.path.insert(0, staged)
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
