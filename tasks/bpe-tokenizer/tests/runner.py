#!/usr/bin/env python3
"""Calls the submitted train_bpe()/encode() on one fixture and reports the
raw results as JSON. Correctness checking against an independent reference
implementation happens entirely in grade.py.
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
        from bpe import train_bpe, encode  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        kind = fixture["kind"]
        if kind == "train":
            merges = train_bpe(fixture["word_freqs"], fixture["num_merges"])
            result = {"ok": True, "merges": [list(p) for p in merges]}
        elif kind == "encode":
            merges = [tuple(p) for p in fixture["merges"]]
            symbols = encode(fixture["word"], merges)
            result = {"ok": True, "symbols": list(symbols)}
        elif kind == "train_and_encode":
            merges = train_bpe(fixture["word_freqs"], fixture["num_merges"])
            encoded = {w: list(encode(w, merges)) for w in fixture["encode_words"]}
            result = {"ok": True, "merges": [list(p) for p in merges], "encoded": encoded}
        else:
            raise ValueError("unknown fixture kind: " + kind)
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
