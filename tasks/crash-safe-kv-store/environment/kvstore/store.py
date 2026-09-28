"""A minimal embedded key-value store.

This implementation is functionally correct when nothing ever interrupts it,
but makes no durability guarantees: it does not fsync, does not checksum
records, does not truncate a torn write on recovery, and compacts by
rewriting the live file in place. See /app/TASK_CONTRACT.md.
"""
import os


class KVStore:
    def __init__(self, path):
        self.path = path
        self._index = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return
        with open(self.path, "rb") as f:
            data = f.read()
        pos = 0
        n = len(data)
        while pos + 9 <= n:
            op = data[pos]
            klen = int.from_bytes(data[pos + 1:pos + 5], "little")
            vlen = int.from_bytes(data[pos + 5:pos + 9], "little")
            end = pos + 9 + klen + vlen
            if end > n:
                break
            key = data[pos + 9:pos + 9 + klen]
            val = data[pos + 9 + klen:end]
            if op == 1:
                self._index[key] = val
            elif op == 2:
                self._index.pop(key, None)
            pos = end

    def _append(self, op, key, value):
        rec = (
            bytes([op])
            + len(key).to_bytes(4, "little")
            + len(value).to_bytes(4, "little")
            + key
            + value
        )
        with open(self.path, "ab") as f:
            f.write(rec)

    def put(self, key, value):
        self._append(1, key, value)
        self._index[key] = value

    def delete(self, key):
        self._append(2, key, b"")
        self._index.pop(key, None)

    def get(self, key):
        return self._index.get(key)

    def iter_items(self):
        return list(self._index.items())

    def compact(self):
        items = list(self._index.items())
        with open(self.path, "wb") as f:
            for key, value in items:
                rec = (
                    bytes([1])
                    + len(key).to_bytes(4, "little")
                    + len(value).to_bytes(4, "little")
                    + key
                    + value
                )
                f.write(rec)

    def close(self):
        pass
