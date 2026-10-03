"""cocotb testbench for the AXI-Lite-style register write slave.

Each test runs the DUT and an independent Python reference model in
lockstep, cycle by cycle, asserting awready/wready/bvalid/regs agree
every cycle -- the reference model is never derived from the DUT itself.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep


class RefModel:
    def __init__(self):
        self.state = "IDLE"
        self.regs = [0, 0, 0, 0]
        self.bvalid = 0

    def step(self, awvalid, awaddr, wvalid, wdata, bready):
        awready = 0
        wready = 0
        if self.state == "IDLE":
            if awvalid and wvalid:
                awready = 1
                wready = 1
                self.regs[awaddr & 3] = wdata & 0xFFFFFFFF
                self.bvalid = 1
                self.state = "RESP"
        else:
            if bready:
                self.bvalid = 0
                self.state = "IDLE"
        return {"awready": awready, "wready": wready, "bvalid": self.bvalid, "regs": list(self.regs)}


async def reset(dut):
    dut.rst_n.value = 0
    dut.awvalid.value = 0
    dut.awaddr.value = 0
    dut.wvalid.value = 0
    dut.wdata.value = 0
    dut.bready.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


def regs_from_flat(flat):
    return [
        flat & 0xFFFFFFFF,
        (flat >> 32) & 0xFFFFFFFF,
        (flat >> 64) & 0xFFFFFFFF,
        (flat >> 96) & 0xFFFFFFFF,
    ]


async def cycle(dut, awvalid=0, awaddr=0, wvalid=0, wdata=0, bready=0):
    dut.awvalid.value = awvalid
    dut.awaddr.value = awaddr
    dut.wvalid.value = wvalid
    dut.wdata.value = wdata
    dut.bready.value = bready
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return {
        "awready": int(dut.awready.value),
        "wready": int(dut.wready.value),
        "bvalid": int(dut.bvalid.value),
        "regs": regs_from_flat(int(dut.regs_flat.value)),
    }


def check(step_i, dut_state, ref_state, ctx):
    for key in ("awready", "wready", "bvalid", "regs"):
        assert dut_state[key] == ref_state[key], (
            "step %d (%s): %s mismatch: dut=%r ref=%r" % (step_i, ctx, key, dut_state[key], ref_state[key])
        )


@cocotb.test()
async def test_basic_write_immediate_bready(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    ops = [
        dict(awvalid=1, awaddr=0, wvalid=1, wdata=0x1111, bready=1),
        dict(bready=1),
        dict(bready=1),
    ]
    for i, op in enumerate(ops):
        dut_state = await cycle(dut, **op)
        ref_state = model.step(op.get("awvalid", 0), op.get("awaddr", 0), op.get("wvalid", 0), op.get("wdata", 0), op.get("bready", 0))
        check(i, dut_state, ref_state, "basic")


@cocotb.test()
async def test_bvalid_holds_through_stall(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    ops = [
        dict(awvalid=1, awaddr=1, wvalid=1, wdata=0x2222, bready=0),
        dict(bready=0),
        dict(bready=0),
        dict(bready=0),
        dict(bready=1),
        dict(bready=0),
    ]
    for i, op in enumerate(ops):
        dut_state = await cycle(dut, **op)
        ref_state = model.step(op.get("awvalid", 0), op.get("awaddr", 0), op.get("wvalid", 0), op.get("wdata", 0), op.get("bready", 0))
        check(i, dut_state, ref_state, "stall")
        if 1 <= i <= 3:
            assert dut_state["bvalid"] == 1, "step %d: bvalid must hold high while bready is low" % i


@cocotb.test()
async def test_register_persistence(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    values = [0xAAAA, 0xBBBB, 0xCCCC, 0xDDDD]
    step = 0
    for addr, val in enumerate(values):
        dut_state = await cycle(dut, awvalid=1, awaddr=addr, wvalid=1, wdata=val, bready=0)
        ref_state = model.step(1, addr, 1, val, 0)
        check(step, dut_state, ref_state, "persist-accept")
        step += 1
        dut_state = await cycle(dut, bready=1)
        ref_state = model.step(0, 0, 0, 0, 1)
        check(step, dut_state, ref_state, "persist-complete")
        step += 1

    assert model.regs == values, "reference model bookkeeping bug if this fails"
    dut_state = await cycle(dut)
    ref_state = model.step(0, 0, 0, 0, 0)
    check(step, dut_state, ref_state, "persist-final")
    assert dut_state["regs"] == values, "all four registers must hold their written values"


@cocotb.test()
async def test_back_to_back_with_varying_stalls(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    writes = [(0, 0x10, 0), (1, 0x20, 2), (2, 0x30, 1), (3, 0x40, 4)]
    step = 0
    for addr, val, stall in writes:
        dut_state = await cycle(dut, awvalid=1, awaddr=addr, wvalid=1, wdata=val, bready=0)
        ref_state = model.step(1, addr, 1, val, 0)
        check(step, dut_state, ref_state, "b2b-accept")
        step += 1
        for _ in range(stall):
            dut_state = await cycle(dut, bready=0)
            ref_state = model.step(0, 0, 0, 0, 0)
            check(step, dut_state, ref_state, "b2b-stall")
            step += 1
        dut_state = await cycle(dut, bready=1)
        ref_state = model.step(0, 0, 0, 0, 1)
        check(step, dut_state, ref_state, "b2b-complete")
        step += 1


@cocotb.test()
async def test_mixed_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    rng = random.Random(24601)
    pending_write = False
    for i in range(150):
        if model.state == "IDLE" and not pending_write and rng.random() < 0.4:
            addr = rng.randint(0, 3)
            val = rng.randint(0, 0xFFFFFFFF)
            op = dict(awvalid=1, awaddr=addr, wvalid=1, wdata=val, bready=0)
            pending_write = True
        elif model.state == "RESP":
            bready = 1 if rng.random() < 0.3 else 0
            op = dict(bready=bready)
            if bready:
                pending_write = False
        else:
            op = dict()
            pending_write = False
        dut_state = await cycle(dut, **op)
        ref_state = model.step(op.get("awvalid", 0), op.get("awaddr", 0), op.get("wvalid", 0), op.get("wdata", 0), op.get("bready", 0))
        check(i, dut_state, ref_state, "mixed-random")
