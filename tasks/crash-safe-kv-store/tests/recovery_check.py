#!/usr/bin/env python3
"""Opens a (possibly just-crashed) store fresh and reports its logical
contents. Optionally performs one more put + close + reopen + get to prove
the store is still usable for future writes after recovery.
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--pkgdir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--probe-key", default=None)
    ap.add_argument("--probe-value", default=None)
    args = ap.parse_args()

    result = {"ok": False}
    try:
        sys.path.insert(0, args.pkgdir)
        from kvstore import KVStore  # noqa: E402

        store = KVStore(args.db)
        items = {k.decode("utf-8"): v.decode("utf-8") for k, v in store.iter_items()}
        result["items"] = items

        if args.probe_key is not None:
            store.put(args.probe_key.encode("utf-8"), args.probe_value.encode("utf-8"))
            store.close()
            store2 = KVStore(args.db)
            got = store2.get(args.probe_key.encode("utf-8"))
            result["probe_roundtrip"] = got == args.probe_value.encode("utf-8")
            store2.close()
        else:
            store.close()

        result["ok"] = True
    except Exception as exc:  # noqa: BLE001
        result["ok"] = False
        result["error"] = repr(exc)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
