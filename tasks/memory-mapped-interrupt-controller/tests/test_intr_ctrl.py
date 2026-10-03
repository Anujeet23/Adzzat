"""cocotb testbench for the interrupt controller.

Each test runs the DUT and an independent Python reference model in
lockstep, cycle by cycle, asserting irq_out/pending/irq_id agree every
cycle -- the reference model is never derived from the DUT itself.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

N = 4


class RefModel:
    def __init__(self, n):
        self.n = n
        self.pending = [0] * n
        self.irq_in_prev = [0] * n
        self.irq_out = 0
        self.irq_id = 0

    def step(self, irq_in, irq_enable, ack):
        chosen = None
        for i in range(self.n):
            if self.pending[i] and irq_enable[i]:
                chosen = i
                break
        new_irq_out = 1 if chosen is not None else 0
        new_irq_id = chosen if chosen is not None else 0

        new_pending = list(self.pending)
        for i in range(self.n):
            if irq_in[i] and not self.irq_in_prev[i]:
                new_pending[i] = 1
        if ack:
            new_pending[self.irq_id] = 0

        self.irq_in_prev = list(irq_in)
        self.pending = new_pending
        self.irq_out = new_irq_out
        self.irq_id = new_irq_id
        return {"irq_out": self.irq_out, "pending": list(self.pending), "irq_id": self.irq_id}


def bits_to_int(bits):
    v = 0
    for i, b in enumerate(bits):
        v |= (b & 1) << i
    return v


def int_to_bits(v, n):
    return [(v >> i) & 1 for i in range(n)]


async def reset(dut):
    dut.rst_n.value = 0
    dut.irq_in.value = 0
    dut.irq_enable.value = 0
    dut.ack.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


async def cycle(dut, irq_in=None, irq_enable=None, ack=0):
    if irq_in is None:
        irq_in = [0] * N
    if irq_enable is None:
        irq_enable = [1] * N
    dut.irq_in.value = bits_to_int(irq_in)
    dut.irq_enable.value = bits_to_int(irq_enable)
    dut.ack.value = ack
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return {
        "irq_out": int(dut.irq_out.value),
        "pending": int_to_bits(int(dut.pending.value), N),
        "irq_id": int(dut.irq_id.value),
    }


def check(step_i, dut_state, ref_state, ctx):
    for key in ("irq_out", "pending", "irq_id"):
        assert dut_state[key] == ref_state[key], (
            "step %d (%s): %s mismatch: dut=%r ref=%r" % (step_i, ctx, key, dut_state[key], ref_state[key])
        )


@cocotb.test()
async def test_sticky_latching(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(N)

    ops = [
        ([1, 0, 0, 0], [1, 1, 1, 1], 0),
        ([0, 0, 0, 0], [1, 1, 1, 1], 0),
        ([0, 0, 0, 0], [1, 1, 1, 1], 0),
        ([0, 0, 0, 0], [1, 1, 1, 1], 0),
    ]
    for i, (irq_in, en, ack) in enumerate(ops):
        dut_state = await cycle(dut, irq_in, en, ack)
        ref_state = model.step(irq_in, en, ack)
        check(i, dut_state, ref_state, "sticky")
    assert dut_state["pending"][0] == 1, "pending must stay set after the pulse ends"


@cocotb.test()
async def test_priority_encoding(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(N)

    ops = [
        ([0, 1, 0, 1], [1, 1, 1, 1], 0),
        ([0, 0, 0, 0], [1, 1, 1, 1], 0),
    ]
    for i, (irq_in, en, ack) in enumerate(ops):
        dut_state = await cycle(dut, irq_in, en, ack)
        ref_state = model.step(irq_in, en, ack)
        check(i, dut_state, ref_state, "priority")
    assert dut_state["irq_id"] == 1, "lowest pending-and-enabled index must win"


@cocotb.test()
async def test_selective_ack(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(N)

    ops = [
        ([1, 0, 0, 0], [1, 1, 1, 1], 0),
        ([0, 0, 0, 0], [1, 1, 1, 1], 0),
        ([0, 0, 1, 0], [1, 1, 1, 1], 0),
        ([0, 0, 0, 0], [1, 1, 1, 1], 0),
    ]
    for i, (irq_in, en, ack) in enumerate(ops):
        dut_state = await cycle(dut, irq_in, en, ack)
        ref_state = model.step(irq_in, en, ack)
        check(i, dut_state, ref_state, "pre-ack")
    assert dut_state["pending"] == [1, 0, 1, 0], "both sources 0 and 2 must be pending before any ack"

    dut_state = await cycle(dut, ack=1)
    ref_state = model.step([0, 0, 0, 0], [1, 1, 1, 1], 1)
    check(4, dut_state, ref_state, "ack")

    dut_state = await cycle(dut)
    ref_state = model.step([0, 0, 0, 0], [1, 1, 1, 1], 0)
    check(5, dut_state, ref_state, "post-ack")
    assert dut_state["pending"][2] == 1, "acking source 0 must not clear source 2's pending bit"
    assert dut_state["pending"][0] == 0, "source 0's own bit must be cleared by its own ack"


@cocotb.test()
async def test_cascading_acks(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(N)

    ops = [
        ([1, 0, 1, 0], [1, 1, 1, 1], 0),
        ([0, 0, 0, 0], [1, 1, 1, 1], 0),
    ]
    for i, (irq_in, en, ack) in enumerate(ops):
        dut_state = await cycle(dut, irq_in, en, ack)
        ref_state = model.step(irq_in, en, ack)
        check(i, dut_state, ref_state, "cascade-setup")
    assert dut_state["irq_id"] == 0

    dut_state = await cycle(dut, ack=1)
    ref_state = model.step([0, 0, 0, 0], [1, 1, 1, 1], 1)
    check(2, dut_state, ref_state, "cascade-ack1")

    dut_state = await cycle(dut)
    ref_state = model.step([0, 0, 0, 0], [1, 1, 1, 1], 0)
    check(3, dut_state, ref_state, "cascade-reveal")
    assert dut_state["irq_out"] == 1 and dut_state["irq_id"] == 2, (
        "after acking source 0, source 2 must now be reported"
    )

    dut_state = await cycle(dut, ack=1)
    ref_state = model.step([0, 0, 0, 0], [1, 1, 1, 1], 1)
    check(4, dut_state, ref_state, "cascade-ack2")

    dut_state = await cycle(dut)
    ref_state = model.step([0, 0, 0, 0], [1, 1, 1, 1], 0)
    check(5, dut_state, ref_state, "cascade-done")
    assert dut_state["irq_out"] == 0, "no sources left pending"


@cocotb.test()
async def test_mixed_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(N)

    rng = random.Random(555)
    for i in range(150):
        irq_in = [1 if rng.random() < 0.1 else 0 for _ in range(N)]
        irq_enable = [1 if rng.random() < 0.8 else 0 for _ in range(N)]
        ack = 1 if rng.random() < 0.2 else 0
        dut_state = await cycle(dut, irq_in, irq_enable, ack)
        ref_state = model.step(irq_in, irq_enable, ack)
        check(i, dut_state, ref_state, "mixed-random")
