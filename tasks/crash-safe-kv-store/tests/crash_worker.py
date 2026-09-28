#!/usr/bin/env python3
"""Runs a scripted operation sequence against a submitted KVStore, with
optional fault injection into kvstore.iolayer: either a simulated kill
(--crash-after), or a synchronous concurrent-reader pause (--pause-after).

Writes a JSON trace of every instrumented iolayer call (call_id, function
name, and which op index it happened during) to --trace-out. On a simulated
kill, the process calls os._exit() immediately -- no further Python code
runs, matching a real hard kill.
"""
import argparse
import itertools
import json
import os
import random
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--pkgdir", required=True)
    ap.add_argument("--ops", required=True)
    ap.add_argument("--trace-out", required=True)
    ap.add_argument("--crash-after", type=int, default=0)
    ap.add_argument("--partial-seed", type=int, default=0)
    ap.add_argument("--pause-after", type=int, default=0)
    ap.add_argument("--pause-out", default=None)
    ap.add_argument("--recovery-script", default=None)
    args = ap.parse_args()

    sys.path.insert(0, args.pkgdir)
    from kvstore import store as store_mod  # noqa: E402
    from kvstore import iolayer  # noqa: E402

    with open(args.ops, "r", encoding="utf-8") as f:
        ops = json.load(f)["ops"]

    counter = itertools.count(1)
    trace = []
    original = {
        name: getattr(iolayer, name)
        for name in ("pwrite_all", "fsync", "atomic_replace", "fsync_dir")
    }
    ctx = {"op_index": -1}

    def flush_trace():
        with open(args.trace_out, "w", encoding="utf-8") as tf:
            json.dump(trace, tf)

    def make_wrapper(name):
        def wrapper(*call_args, **call_kwargs):
            call_id = next(counter)
            trace.append({"call_id": call_id, "fn": name, "op_index": ctx["op_index"]})

            if args.pause_after and call_id == args.pause_after:
                flush_trace()
                subprocess.run(
                    [
                        sys.executable,
                        args.recovery_script,
                        "--db",
                        args.db,
                        "--pkgdir",
                        args.pkgdir,
                        "--out",
                        args.pause_out,
                    ],
                    check=False,
                    capture_output=True,
                    timeout=60,
                )

            if args.crash_after and call_id == args.crash_after:
                if name == "pwrite_all" and len(call_args) >= 2:
                    fd, data = call_args[0], call_args[1]
                    rng = random.Random(args.partial_seed)
                    n = rng.randint(0, len(data))
                    if n:
                        try:
                            os.write(fd, data[:n])
                        except OSError:
                            pass
                flush_trace()
                os._exit(137)

            return original[name](*call_args, **call_kwargs)

        return wrapper

    for name in original:
        setattr(iolayer, name, make_wrapper(name))

    kv = store_mod.KVStore(args.db)
    for i, op in enumerate(ops):
        ctx["op_index"] = i
        kind = op["op"]
        if kind == "put":
            kv.put(op["key"].encode("utf-8"), op["value"].encode("utf-8"))
        elif kind == "delete":
            kv.delete(op["key"].encode("utf-8"))
        elif kind == "get":
            kv.get(op["key"].encode("utf-8"))
        elif kind == "compact":
            kv.compact()
        else:
            raise ValueError("unknown op: " + kind)
    kv.close()

    flush_trace()
    print("DONE")


if __name__ == "__main__":
    main()
