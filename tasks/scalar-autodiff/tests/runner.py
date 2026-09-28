#!/usr/bin/env python3
"""Builds one of several computation graphs with the submission's Value
class, calls backward(), and reports every leaf's .grad as JSON. The
mirrored plain-float versions of these same graphs live in grade.py's
CASES_FLOAT table and are used there, independently, for the finite-
difference ground truth -- this runner never computes that itself.
"""
import argparse
import json
import sys


def build_chain(V, leaves):
    x, w = leaves["x"], leaves["w"]
    y = (x * w + 5) / 3 - 1
    return y


def build_diamond(V, leaves):
    x = leaves["x"]
    t = x * x
    u = x * t
    y = t + u
    return y


def build_loop_sum(V, leaves):
    s = leaves["b"]
    for i in range(3):
        s = s + leaves["x%d" % i] * leaves["w%d" % i]
    return s


def build_nonlinear(V, leaves):
    x, y = leaves["x"], leaves["y"]
    a = x.tanh()
    b = y.exp()
    c = a * b + a.relu()
    out = c * c
    return out


def build_mixed_mlp(V, leaves):
    x1, x2 = leaves["x1"], leaves["x2"]
    h1 = (x1 * leaves["w11"] + x2 * leaves["w21"] + leaves["b1"]).tanh()
    h2 = (x1 * leaves["w12"] + x2 * leaves["w22"] + leaves["b2"]).tanh()
    out = h1 * leaves["wo1"] + h2 * leaves["wo2"] + leaves["bo"]
    return out


CASES = {
    "chain": build_chain,
    "diamond": build_diamond,
    "loop_sum": build_loop_sum,
    "nonlinear": build_nonlinear,
    "mixed_mlp": build_mixed_mlp,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkgdir", required=True)
    ap.add_argument("--ops", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    result = {"ok": False}
    try:
        sys.path.insert(0, args.pkgdir)
        from autodiff import Value  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        case = fixture["case"]
        leaf_values = fixture["leaves"]
        leaves = {name: Value(v) for name, v in leaf_values.items()}

        out = CASES[case](Value, leaves)
        out.backward()

        grads = {name: leaves[name].grad for name in leaf_values}
        result = {"ok": True, "output": out.data, "grads": grads}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
