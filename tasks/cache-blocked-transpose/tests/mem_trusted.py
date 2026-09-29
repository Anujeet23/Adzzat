"""Trusted, grader-authoritative copy of kernel/mem.py. The verifier always
substitutes this file over whatever the submission provided at that path
before importing the submission's kernel package, so the simulated cache's
hit/miss accounting cannot be tampered with by a submission that reports
its own, more favorable stats().
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
