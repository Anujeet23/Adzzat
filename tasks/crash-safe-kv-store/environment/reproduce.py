"""Demonstrates the current implementation's data-loss bug.

A torn write (the process dies mid-append, leaving a partial trailing
record) is simulated by hand here. The store does not detect or truncate
the torn tail on recovery, so a later, fully-successful put is appended
*after* the garbage -- and then silently disappears, because replay stops
at the first record it cannot parse and never reaches it again.
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from kvstore import KVStore  # noqa: E402


def main():
    d = tempfile.mkdtemp()
    path = os.path.join(d, "store.db")
    try:
        store = KVStore(path)
        store.put(b"alpha", b"1")
        store.put(b"beta", b"2")
        store.close()

        # Simulate a process killed mid-write: a truncated, unparseable
        # trailing record gets left on disk.
        with open(path, "ab") as f:
            f.write(b"\x01\xff\xff\x00\x00garbage-tail-not-a-full-record")

        store = KVStore(path)
        print("after simulated crash, visible keys:", sorted(store.iter_items()))

        # A brand new write, fully completed with no interruption at all.
        store.put(b"gamma", b"3")
        store.close()

        store = KVStore(path)
        value = store.get(b"gamma")
        print("gamma after reopen:", value)
        if value != b"3":
            print("BUG REPRODUCED: a fully-written key vanished after reopen.")
        else:
            print("not reproduced this run.")
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    main()
