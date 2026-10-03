"""cocotb testbench for the round-robin arbiter.

Each test runs the DUT and an independent Python reference model in
lockstep, cycle by cycle, feeding the same req pattern to both and
asserting grant agrees every cycle -- the reference model is never
derived from the DUT itself.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

N = 4


class RefModel:
    def __init__(self, n):
        self.n = n
        self.ptr = 0

    def step(self, req_bits):
        chosen = None
        for i in range(self.n):
            idx = (self.ptr + i) % self.n
            if req_bits[idx]:
                chosen = idx
                break
        grant = [0] * self.n
        if chosen is not None:
            grant[chosen] = 1
            self.ptr = (chosen + 1) % self.n
        return grant


def bits_to_int(bits):
    v = 0
    for i, b in enumerate(bits):
        v |= (b & 1) << i
    return v


def int_to_bits(v, n):
    return [(v >> i) & 1 for i in range(n)]


async def reset(dut):
    dut.rst_n.value = 0
    dut.req.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


async def cycle(dut, req_bits):
    dut.req.value = bits_to_int(req_bits)
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return int_to_bits(int(dut.grant.value), N)


def check(step_i, dut_grant, ref_grant, ctx):
    assert dut_grant == ref_grant, "step %d (%s): grant mismatch: dut=%r ref=%r" % (step_i, ctx, dut_grant, ref_grant)


@cocotb.test()
async def test_single_requester(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(N)

    for i in range(N):
        req = [0] * N
        req[i] = 1
        dut_grant = await cycle(dut, req)
        ref_grant = model.step(req)
        check(i, dut_grant, ref_grant, "single-%d" % i)


@cocotb.test()
async def test_fairness_full_contention(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(N)

    req = [1] * N
    grants_seen = []
    for i in range(3 * N):
        dut_grant = await cycle(dut, req)
        ref_grant = model.step(req)
        check(i, dut_grant, ref_grant, "full-contention")
        grants_seen.append(dut_grant.index(1))

    for rotation in range(3):
        window = grants_seen[rotation * N : (rotation + 1) * N]
        assert sorted(window) == list(range(N)), (
            "rotation %d: expected each requester granted exactly once, got %r" % (rotation, window)
        )


@cocotb.test()
async def test_partial_contention(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(N)

    req = [0, 1, 0, 1]  # only requesters 1 and 3
    for i in range(10):
        dut_grant = await cycle(dut, req)
        ref_grant = model.step(req)
        check(i, dut_grant, ref_grant, "partial")
        assert dut_grant[0] == 0 and dut_grant[2] == 0, "step %d: non-requesting lines must never be granted" % i


@cocotb.test()
async def test_dynamic_requests(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(N)

    schedule = [
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 1],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1],
        [0, 0, 0, 0],
        [1, 1, 1, 1],
    ]
    for i, req in enumerate(schedule):
        dut_grant = await cycle(dut, req)
        ref_grant = model.step(req)
        check(i, dut_grant, ref_grant, "dynamic")


@cocotb.test()
async def test_mixed_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(N)

    rng = random.Random(2468)
    for i in range(150):
        req = [rng.randint(0, 1) for _ in range(N)]
        dut_grant = await cycle(dut, req)
        ref_grant = model.step(req)
        check(i, dut_grant, ref_grant, "mixed-random")
