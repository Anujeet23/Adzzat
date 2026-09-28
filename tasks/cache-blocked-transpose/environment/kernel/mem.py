"""Simulated memory system with a small, fixed-capacity cache.

Two flat, row-major arrays are addressable: array 0 (source) and array 1
(destination). `transpose(n)` must perform every element access through
`read(array_id, index)` / `write(array_id, index, value)` below, called via
the module reference (`from . import mem; mem.read(...)`), not
`from .mem import read`. The grading harness wraps these two functions to
simulate a direct-mapped-style LRU cache: addresses are grouped into
fixed-size lines, and accessing a line not currently resident is a "miss"
that evicts the least-recently-used resident line if the cache is full.

`set_array`, `get_array`, and `reset` are grading-support functions for
setting up input and reading back output; they do not go through the
simulated cache and are not meant to be called from inside `transpose`.
"""

BLOCK_SIZE = 8
NUM_LINES = 64

_arrays = {}
_lru = []
_resident = set()
_misses = 0
_accesses = 0


def _touch(array_id, index):
    global _misses, _accesses
    _accesses += 1
    key = (array_id, index // BLOCK_SIZE)
    if key in _resident:
        _lru.remove(key)
        _lru.append(key)
    else:
        _misses += 1
        if len(_lru) >= NUM_LINES:
            evict = _lru.pop(0)
            _resident.discard(evict)
        _lru.append(key)
        _resident.add(key)


def read(array_id, index):
    _touch(array_id, index)
    return _arrays[array_id][index]


def write(array_id, index, value):
    _touch(array_id, index)
    _arrays[array_id][index] = value


def set_array(array_id, values):
    _arrays[array_id] = list(values)


def get_array(array_id):
    return list(_arrays[array_id])


def reset():
    global _misses, _accesses, _lru, _resident
    _misses = 0
    _accesses = 0
    _lru = []
    _resident = set()


def stats():
    return {"misses": _misses, "accesses": _accesses}
