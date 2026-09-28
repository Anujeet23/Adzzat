#!/usr/bin/env python3
"""Calls the submitted beam_search() on one or more transition tables and
reports the raw results as JSON. Correctness checking against an
independent reference implementation happens entirely in grade.py.
"""
import argparse
import json
import sys


def run_one(beam_search, case):
    table = {int(k): v for k, v in case["transition_logprobs"].items()}
    result = beam_search(
        table,
        case["start_token"],
        case["end_token"],
        case["vocab_size"],
        case["beam_width"],
        case["max_length"],
    )
    return [{"sequence": list(seq), "raw_logprob": float(score)} for seq, score in result]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkgdir", required=True)
    ap.add_argument("--ops", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    result = {"ok": False}
    try:
        sys.path.insert(0, args.pkgdir)
        from beamsearch import beam_search  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        if "cases" in fixture:
            cases = fixture["cases"]
        else:
            cases = [fixture]

        outputs = [run_one(beam_search, case) for case in cases]
        result = {"ok": True, "results": outputs}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
