"""Scalar-multiplication primitive.

Every scalar multiplication your matmul implementation performs -- at any
level of recursion -- must go through this function, called via the module
reference (`from . import ops; ops.mul(x, y)`), not `from .ops import mul`.
The grading harness counts calls to this exact attribute to measure how
many scalar multiplications your algorithm actually performs; binding the
name into another module's local namespace defeats that instrumentation.
"""


def mul(a: float, b: float) -> float:
    return a * b
