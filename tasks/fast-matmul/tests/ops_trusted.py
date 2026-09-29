"""Trusted, grader-authoritative copy of kernel/ops.py. The verifier always
substitutes this file over whatever the submission provided at that path
before importing the submission's kernel package, so the Sealed type and
its multiplication-only-via-ops.mul restriction cannot be tampered with.
"""


def _value(x):
    return x._value if isinstance(x, Sealed) else float(x)


class Sealed:
    __slots__ = ("_value",)

    def __init__(self, value):
        self._value = _value(value)

    def __repr__(self):
        return "Sealed(%r)" % self._value

    def __float__(self):
        return self._value

    def __eq__(self, other):
        return self._value == _value(other)

    def __add__(self, other):
        return Sealed(self._value + _value(other))

    __radd__ = __add__

    def __sub__(self, other):
        return Sealed(self._value - _value(other))

    def __rsub__(self, other):
        return Sealed(_value(other) - self._value)

    def __neg__(self):
        return Sealed(-self._value)

    def __mul__(self, other):
        raise TypeError("Sealed values cannot be multiplied with * -- call ops.mul(a, b) instead")

    __rmul__ = __mul__


def mul(a, b):
    return Sealed(_value(a) * _value(b))
