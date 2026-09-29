#!/usr/bin/env python3
"""Runs the submitted matmul() on a fixture matrix pair, counting calls to
kernel.ops.mul, and reports the result matrix plus the call count as JSON.

Before importing, the submission's kernel package is copied to a writable
staging directory and its kernel/ops.py is replaced with this grader's own
trusted copy (ops_trusted.py, next to this file) -- so whatever the
submission wrote at kernel/ops.py is never actually used; only
kernel/matmul.py is graded. Matrix elements are wrapped as ops.Sealed
before the call, so the submission cannot compute a correct product
without routing every multiplication through the (now-trusted,
instrumented) ops.mul.
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
    trusted_ops = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ops_trusted.py")
    shutil.copyfile(trusted_ops, os.path.join(staged, "kernel", "ops.py"))
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
        import kernel.ops as ops_mod  # noqa: E402
        from kernel import matmul  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        def wrap(matrix):
            return [[ops_mod.Sealed(x) for x in row] for row in matrix]

        def unwrap(matrix):
            return [[float(x) for x in row] for row in matrix]

        original = ops_mod.mul
        count = [0]

        def counted(a, b):
            count[0] += 1
            return original(a, b)

        ops_mod.mul = counted

        A = wrap(fixture["A"])
        B = wrap(fixture["B"])
        C = matmul(A, B)

        result = {"ok": True, "C": unwrap(C), "mul_count": count[0]}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
