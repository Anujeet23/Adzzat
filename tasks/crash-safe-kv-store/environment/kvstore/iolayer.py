"""Durability primitives.

Every disk write, fsync, atomic rename, and directory fsync that a KVStore
implementation relies on for durability MUST be performed by calling these
functions through the module reference, e.g.:

    from . import iolayer
    iolayer.pwrite_all(fd, data)

Not:

    from .iolayer import pwrite_all
    pwrite_all(fd, data)

The grading harness instruments these four entry points (by replacing the
attributes on this module object) to simulate a process being killed at an
exact point during a call. Binding the names into another module's local
namespace via `from .iolayer import X` defeats that instrumentation, and any
write performed that way will not be recognized as durable by the grader.
"""
import os


def pwrite_all(fd: int, data: bytes) -> None:
    """Write every byte of `data` to `fd` at its current file position."""
    mv = memoryview(data)
    total = 0
    length = len(mv)
    while total < length:
        n = os.write(fd, mv[total:])
        if n <= 0:
            raise OSError("short write")
        total += n


def fsync(fd: int) -> None:
    """Flush `fd`'s content to durable storage."""
    os.fsync(fd)


def atomic_replace(src: str, dst: str) -> None:
    """Atomically make `dst` refer to `src`'s content, in one filesystem step."""
    os.replace(src, dst)


def fsync_dir(dir_path: str) -> None:
    """Flush a directory's metadata (e.g. after a rename inside it) to durable storage.

    Directory fsync is a POSIX concept; on Windows this is a no-op, since the
    grading container is always Linux.
    """
    if os.name == "nt":
        return
    fd = os.open(dir_path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
