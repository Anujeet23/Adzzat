"""Reference crash-safe implementation. Author-only; not shipped to agents.

Format: a sequence of records, each
    MAGIC(1) | op(1) | key_len(4 LE) | val_len(4 LE) | key | val | crc32(4 LE)
where crc32 covers everything from op through val. On load, records are
replayed from the start; the first record that doesn't fully fit or whose
checksum doesn't match ends replay, and the file is truncated to the end of
the last valid record so a subsequent append can never be shadowed by a
torn tail. Compaction writes a full new file to a temp path, fsyncs it,
atomically renames it over the live file, then fsyncs the containing
directory -- so a compact() call never changes what get()/iter_items() see,
regardless of when it's interrupted.
"""
import os
import zlib

from . import iolayer

# os.open() defaults to CRT text-mode translation on Windows unless O_BINARY
# is set, silently mangling any 0x0A byte in binary data (e.g. inside a crc32
# field). This is a no-op on POSIX, where the grading container always runs.
_BINARY = getattr(os, "O_BINARY", 0)

MAGIC = b"K"
OP_PUT = 1
OP_DEL = 2
HEADER_LEN = 1 + 1 + 4 + 4  # magic + op + klen + vlen


def _replay(path):
    index = {}
    if not os.path.exists(path):
        return index, 0
    with open(path, "rb") as f:
        data = f.read()
    n = len(data)
    pos = 0
    valid_end = 0
    while pos + HEADER_LEN <= n:
        if data[pos:pos + 1] != MAGIC:
            break
        op = data[pos + 1]
        klen = int.from_bytes(data[pos + 2:pos + 6], "little")
        vlen = int.from_bytes(data[pos + 6:pos + 10], "little")
        body_end = pos + HEADER_LEN + klen + vlen
        if body_end + 4 > n:
            break
        body = data[pos + 1:body_end]
        crc_stored = int.from_bytes(data[body_end:body_end + 4], "little")
        if zlib.crc32(body) != crc_stored:
            break
        key = data[pos + HEADER_LEN:pos + HEADER_LEN + klen]
        val = data[pos + HEADER_LEN + klen:body_end]
        if op == OP_PUT:
            index[key] = val
        elif op == OP_DEL:
            index.pop(key, None)
        pos = body_end + 4
        valid_end = pos
    return index, valid_end


def _encode(op, key, value):
    body = bytes([op]) + len(key).to_bytes(4, "little") + len(value).to_bytes(4, "little") + key + value
    return MAGIC + body + zlib.crc32(body).to_bytes(4, "little")


class KVStore:
    def __init__(self, path):
        self.path = path
        self._index, valid_end = _replay(path)
        if os.path.exists(path):
            size = os.path.getsize(path)
            if valid_end < size:
                fd = os.open(path, os.O_WRONLY | _BINARY)
                try:
                    os.ftruncate(fd, valid_end)
                    iolayer.fsync(fd)
                finally:
                    os.close(fd)

    def _append(self, rec):
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | _BINARY, 0o644)
        try:
            iolayer.pwrite_all(fd, rec)
            iolayer.fsync(fd)
        finally:
            os.close(fd)

    def put(self, key, value):
        self._append(_encode(OP_PUT, key, value))
        self._index[key] = value

    def delete(self, key):
        self._append(_encode(OP_DEL, key, b""))
        self._index.pop(key, None)

    def get(self, key):
        return self._index.get(key)

    def iter_items(self):
        return list(self._index.items())

    def compact(self):
        directory = os.path.dirname(os.path.abspath(self.path)) or "."
        tmp_path = self.path + ".compact.tmp"
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | _BINARY, 0o644)
        try:
            for key, value in self._index.items():
                iolayer.pwrite_all(fd, _encode(OP_PUT, key, value))
            iolayer.fsync(fd)
        finally:
            os.close(fd)
        iolayer.atomic_replace(tmp_path, self.path)
        iolayer.fsync_dir(directory)

    def close(self):
        pass
