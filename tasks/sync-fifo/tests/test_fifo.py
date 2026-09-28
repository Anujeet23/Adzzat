"""cocotb testbench for the synchronous FIFO.

Each test runs the DUT and an independent Python reference model in
lockstep, cycle by cycle, and asserts full/empty/rd_data agree after
every cycle -- the reference model is never derived from the DUT itself.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

DEPTH = 8
WIDTH = 8


class RefModel:
    def __init__(self, depth):
        self.depth = depth
        self.mem = []
        self.rd_data = 0

    def step(self, wr_en, wr_data, rd_en):
        full = len(self.mem) == self.depth
        empty = len(self.mem) == 0
        rd_fire = bool(rd_en) and not empty
        wr_fire = bool(wr_en) and (not full or rd_fire)
        if rd_fire:
            self.rd_data = self.mem.pop(0)
        if wr_fire:
            self.mem.append(wr_data & ((1 << WIDTH) - 1))
        return {
            "full": len(self.mem) == self.depth,
            "empty": len(self.mem) == 0,
            "rd_data": self.rd_data,
        }


async def reset(dut):
    dut.rst_n.value = 0
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


async def cycle(dut, wr_en=0, wr_data=0, rd_en=0):
    dut.wr_en.value = wr_en
    dut.wr_data.value = wr_data
    dut.rd_en.value = rd_en
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return {
        "full": bool(dut.full.value),
        "empty": bool(dut.empty.value),
        "rd_data": int(dut.rd_data.value),
    }


def check(step, dut_state, ref_state, ctx):
    for key in ("full", "empty"):
        assert dut_state[key] == ref_state[key], (
            "step %d (%s): %s mismatch: dut=%r ref=%r" % (step, ctx, key, dut_state[key], ref_state[key])
        )
    if ref_state.get("check_rd_data", True):
        assert dut_state["rd_data"] == ref_state["rd_data"], (
            "step %d (%s): rd_data mismatch: dut=%r ref=%r" % (step, ctx, dut_state["rd_data"], ref_state["rd_data"])
        )


@cocotb.test()
async def test_basic_write_read(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(DEPTH)

    values = [0x11, 0x22, 0x33]
    for i, v in enumerate(values):
        dut_state = await cycle(dut, wr_en=1, wr_data=v)
        ref_state = model.step(1, v, 0)
        check(i, dut_state, ref_state, "write")

    for i, v in enumerate(values):
        dut_state = await cycle(dut, rd_en=1)
        ref_state = model.step(0, 0, 1)
        check(i, dut_state, ref_state, "read")


@cocotb.test()
async def test_full_empty_flags(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(DEPTH)

    for i in range(DEPTH):
        dut_state = await cycle(dut, wr_en=1, wr_data=i)
        ref_state = model.step(1, i, 0)
        check(i, dut_state, ref_state, "fill")
    assert bool(dut.full.value), "expected full after writing DEPTH items"

    for i in range(DEPTH):
        dut_state = await cycle(dut, rd_en=1)
        ref_state = model.step(0, 0, 1)
        check(i, dut_state, ref_state, "drain")
    assert bool(dut.empty.value), "expected empty after draining all items"


@cocotb.test()
async def test_wraparound(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(DEPTH)

    rng = random.Random(1234)
    for step in range(120):
        wr_en = rng.random() < 0.6
        rd_en = rng.random() < 0.5
        wr_data = rng.randint(0, 255)
        dut_state = await cycle(dut, wr_en=int(wr_en), wr_data=wr_data, rd_en=int(rd_en))
        ref_state = model.step(int(wr_en), wr_data, int(rd_en))
        check(step, dut_state, ref_state, "random")


@cocotb.test()
async def test_simultaneous_full_write_read(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(DEPTH)

    for i in range(DEPTH):
        dut_state = await cycle(dut, wr_en=1, wr_data=i)
        ref_state = model.step(1, i, 0)
        check(i, dut_state, ref_state, "fill")

    for i in range(DEPTH):
        new_val = 100 + i
        dut_state = await cycle(dut, wr_en=1, wr_data=new_val, rd_en=1)
        ref_state = model.step(1, new_val, 1)
        check(i, dut_state, ref_state, "simultaneous-at-full")
        assert dut_state["full"], "step %d: expected to remain full during simultaneous write+read" % i

    for i in range(DEPTH):
        dut_state = await cycle(dut, rd_en=1)
        ref_state = model.step(0, 0, 1)
        check(i, dut_state, ref_state, "final-drain")
    assert bool(dut.empty.value), "expected empty after final drain"


@cocotb.test()
async def test_simultaneous_empty_write_read(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(DEPTH)

    dut_state = await cycle(dut, wr_en=1, wr_data=0x55, rd_en=1)
    ref_state = model.step(1, 0x55, 1)
    check(0, dut_state, ref_state, "simultaneous-at-empty")
    assert not dut_state["empty"], "expected not empty after write succeeds during simultaneous op at empty"

    dut_state = await cycle(dut, rd_en=1)
    ref_state = model.step(0, 0, 1)
    check(1, dut_state, ref_state, "readback")
    assert dut_state["rd_data"] == 0x55, "expected to read back the value written during the empty+simultaneous cycle"
