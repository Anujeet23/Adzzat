"""cocotb testbench for the programmable-modulus counter.

Each test runs the DUT and an independent Python reference model in
lockstep, cycle by cycle, and asserts count/overflow agree after every
cycle -- the reference model is never derived from the DUT itself.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

WIDTH = 8
MASK = (1 << WIDTH) - 1


class RefModel:
    def __init__(self):
        self.count = 0
        self.modulus = 0

    def step(self, load, mod_in, en):
        overflow = 0
        if load:
            self.modulus = mod_in & MASK
            self.count = 0
        elif en:
            if self.modulus >= 1 and self.count == self.modulus - 1:
                self.count = 0
                overflow = 1
            else:
                self.count = (self.count + 1) & MASK
        return {"count": self.count, "overflow": overflow}


async def reset(dut):
    dut.rst_n.value = 0
    dut.load.value = 0
    dut.mod_in.value = 0
    dut.en.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


async def cycle(dut, load=0, mod_in=0, en=0):
    dut.load.value = load
    dut.mod_in.value = mod_in
    dut.en.value = en
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return {"count": int(dut.count.value), "overflow": int(dut.overflow.value)}


def check(step, dut_state, ref_state, ctx):
    for key in ("count", "overflow"):
        assert dut_state[key] == ref_state[key], (
            "step %d (%s): %s mismatch: dut=%r ref=%r" % (step, ctx, key, dut_state[key], ref_state[key])
        )


@cocotb.test()
async def test_basic_count(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    dut_state = await cycle(dut, load=1, mod_in=5)
    ref_state = model.step(1, 5, 0)
    check(0, dut_state, ref_state, "load")

    for i in range(12):
        dut_state = await cycle(dut, en=1)
        ref_state = model.step(0, 0, 1)
        check(i, dut_state, ref_state, "count")


@cocotb.test()
async def test_load_resets_count(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    dut_state = await cycle(dut, load=1, mod_in=8)
    ref_state = model.step(1, 8, 0)
    check(0, dut_state, ref_state, "load")

    for i in range(5):
        dut_state = await cycle(dut, en=1)
        ref_state = model.step(0, 0, 1)
        check(i, dut_state, ref_state, "count-before-reload")

    dut_state = await cycle(dut, load=1, mod_in=3)
    ref_state = model.step(1, 3, 0)
    check(0, dut_state, ref_state, "reload")
    assert dut_state["count"] == 0, "count must be reset to 0 on the same cycle as load"

    for i in range(7):
        dut_state = await cycle(dut, en=1)
        ref_state = model.step(0, 0, 1)
        check(i, dut_state, ref_state, "count-after-reload")


@cocotb.test()
async def test_overflow_timing(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    for modulus in (4, 1, 6):
        dut_state = await cycle(dut, load=1, mod_in=modulus)
        ref_state = model.step(1, modulus, 0)
        check(0, dut_state, ref_state, "load-%d" % modulus)
        for i in range(3 * modulus + 2):
            dut_state = await cycle(dut, en=1)
            ref_state = model.step(0, 0, 1)
            check(i, dut_state, ref_state, "overflow-modulus-%d" % modulus)


@cocotb.test()
async def test_pause_resume(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    dut_state = await cycle(dut, load=1, mod_in=6)
    ref_state = model.step(1, 6, 0)
    check(0, dut_state, ref_state, "load")

    for i in range(3):
        dut_state = await cycle(dut, en=1)
        ref_state = model.step(0, 0, 1)
        check(i, dut_state, ref_state, "pre-pause")

    for i in range(4):
        dut_state = await cycle(dut, en=0)
        ref_state = model.step(0, 0, 0)
        check(i, dut_state, ref_state, "paused")

    for i in range(10):
        dut_state = await cycle(dut, en=1)
        ref_state = model.step(0, 0, 1)
        check(i, dut_state, ref_state, "post-pause")


@cocotb.test()
async def test_mixed_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    dut_state = await cycle(dut, load=1, mod_in=7)
    ref_state = model.step(1, 7, 0)
    check(0, dut_state, ref_state, "initial-load")

    rng = random.Random(4242)
    for step in range(150):
        load = rng.random() < 0.08
        mod_in = rng.randint(1, 15) if load else 0
        en = rng.random() < 0.7
        dut_state = await cycle(dut, load=int(load), mod_in=mod_in, en=int(en))
        ref_state = model.step(int(load), mod_in, int(en))
        check(step, dut_state, ref_state, "random")
