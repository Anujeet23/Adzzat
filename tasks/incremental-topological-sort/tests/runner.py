#!/usr/bin/env python3
"""Executes a scripted sequence of add_node/add_edge/order_check operations
against the submitted DAG, validating the *property* that order() is a
valid topological order of a known node/edge set tracked independently
by this runner from the fixture's own expected outcomes -- not one exact
expected list.
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
        from toposort import DAG  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        dag = DAG()
        known_nodes = set()
        known_edges = set()

        for step, op in enumerate(fixture["ops"]):
            kind = op["op"]

            if kind == "add_node":
                dag.add_node(op["node"])
                known_nodes.add(op["node"])

            elif kind == "add_edge":
                u, v = op["u"], op["v"]
                got = dag.add_edge(u, v)
                if got != op["expect"]:
                    raise AssertionError(
                        "add_edge(%r, %r) at step %d: expected %s, got %s"
                        % (u, v, step, op["expect"], got)
                    )
                known_nodes.add(u)
                known_nodes.add(v)
                if op["expect"]:
                    known_edges.add((u, v))

            elif kind == "order_check":
                order = dag.order()
                if len(order) != len(known_nodes) or set(order) != known_nodes:
                    raise AssertionError(
                        "order() at step %d is not a permutation of the known nodes %r: got %r"
                        % (step, sorted(known_nodes), order)
                    )
                pos = {n: i for i, n in enumerate(order)}
                for u, v in known_edges:
                    if pos[u] >= pos[v]:
                        raise AssertionError(
                            "order() at step %d violates edge %r -> %r: %r" % (step, u, v, order)
                        )

            else:
                raise ValueError("unknown op: " + kind)

        result = {"ok": True, "final_order": dag.order()}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
