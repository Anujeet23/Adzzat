"""cocotb testbench for the direct-mapped cache controller.

Every check goes through the external req/we/addr/wdata/hit/rdata
interface only -- no internal signal is ever inspected. An independent
Python reference model implements the same cache+backing-store
semantics and is run in lockstep with the DUT.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

ADDR_WIDTH = 8
INDEX_WIDTH = 3
DATA_WIDTH = 8
LINES = 1 << INDEX_WIDTH
DATA_MASK = (1 << DATA_WIDTH) - 1


class RefModel:
    def __init__(self):
        self.mem = {k: k & DATA_MASK for k in range(1 << ADDR_WIDTH)}
        self.valid = [False] * LINES
        self.dirty = [False] * LINES
        self.tag = [0] * LINES
        self.data = [0] * LINES

    def _split(self, addr):
        index = addr & (LINES - 1)
        tag = addr >> INDEX_WIDTH
        return tag, index

    def step(self, we, addr, wdata):
        tag, index = self._split(addr)
        hit = self.valid[index] and self.tag[index] == tag
        if hit:
            if we:
                self.data[index] = wdata & DATA_MASK
                self.dirty[index] = True
                rdata = None
            else:
                rdata = self.data[index]
        else:
            if self.valid[index] and self.dirty[index]:
                old_addr = (self.tag[index] << INDEX_WIDTH) | index
                self.mem[old_addr] = self.data[index]
            self.valid[index] = True
            self.tag[index] = tag
            if we:
                self.data[index] = wdata & DATA_MASK
                self.dirty[index] = True
                rdata = wdata & DATA_MASK
            else:
                self.data[index] = self.mem[addr]
                self.dirty[index] = False
                rdata = self.data[index]
        return {"hit": 1 if hit else 0, "rdata": rdata}


async def reset(dut):
    dut.rst_n.value = 0
    dut.req.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.wdata.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


async def access(dut, we, addr, wdata=0):
    dut.req.value = 1
    dut.we.value = we
    dut.addr.value = addr
    dut.wdata.value = wdata
    await RisingEdge(dut.clk)
    dut.req.value = 0
    await NextTimeStep()
    return {"hit": int(dut.hit.value), "rdata": int(dut.rdata.value)}


def check(step_i, dut_state, ref_state, ctx, check_rdata=True):
    assert dut_state["hit"] == ref_state["hit"], (
        "step %d (%s): hit mismatch: dut=%r ref=%r" % (step_i, ctx, dut_state["hit"], ref_state["hit"])
    )
    if check_rdata and ref_state["rdata"] is not None:
        assert dut_state["rdata"] == ref_state["rdata"], (
            "step %d (%s): rdata mismatch: dut=%r ref=%r" % (step_i, ctx, dut_state["rdata"], ref_state["rdata"])
        )


@cocotb.test()
async def test_basic_hit_miss(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    addr = 5
    dut_state = await access(dut, we=0, addr=addr)
    ref_state = model.step(0, addr, 0)
    check(0, dut_state, ref_state, "cold-miss")
    assert dut_state["hit"] == 0, "first access to a fresh cache must be a miss"

    dut_state = await access(dut, we=0, addr=addr)
    ref_state = model.step(0, addr, 0)
    check(1, dut_state, ref_state, "repeat-hit")
    assert dut_state["hit"] == 1, "repeated access to the same address must hit"


@cocotb.test()
async def test_write_then_read_hit(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    addr = 10
    dut_state = await access(dut, we=1, addr=addr, wdata=0x77)
    ref_state = model.step(1, addr, 0x77)
    check(0, dut_state, ref_state, "write-miss", check_rdata=True)

    dut_state = await access(dut, we=0, addr=addr)
    ref_state = model.step(0, addr, 0)
    check(1, dut_state, ref_state, "read-back-hit")
    assert dut_state["rdata"] == 0x77, "read-back must return the written value, not the stale seed"


@cocotb.test()
async def test_dirty_writeback_on_eviction(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    addr_a = 16  # index 0, tag 2
    addr_b = 24  # index 0, tag 3

    dut_state = await access(dut, we=1, addr=addr_a, wdata=0x5A)
    ref_state = model.step(1, addr_a, 0x5A)
    check(0, dut_state, ref_state, "write-a")

    dut_state = await access(dut, we=0, addr=addr_b)
    ref_state = model.step(0, addr_b, 0)
    check(1, dut_state, ref_state, "evict-a-with-b")

    dut_state = await access(dut, we=0, addr=addr_a)
    ref_state = model.step(0, addr_a, 0)
    check(2, dut_state, ref_state, "refetch-a-after-eviction")
    assert dut_state["rdata"] == 0x5A, (
        "re-fetching address %d after its dirty line was evicted must see the "
        "written value 0x5a, not the original seed" % addr_a
    )


@cocotb.test()
async def test_clean_eviction(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    addr_a = 32  # index 0, tag 4
    addr_b = 40  # index 0, tag 5

    dut_state = await access(dut, we=0, addr=addr_a)
    ref_state = model.step(0, addr_a, 0)
    check(0, dut_state, ref_state, "clean-read-a")

    dut_state = await access(dut, we=0, addr=addr_b)
    ref_state = model.step(0, addr_b, 0)
    check(1, dut_state, ref_state, "evict-clean-a")

    dut_state = await access(dut, we=0, addr=addr_a)
    ref_state = model.step(0, addr_a, 0)
    check(2, dut_state, ref_state, "refetch-clean-a")
    assert dut_state["rdata"] == (addr_a & DATA_MASK), "a never-written line's eviction must not alter its seed value"


@cocotb.test()
async def test_mixed_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()

    # Shifted well clear of every address used by the earlier tests in this
    # file: all @cocotb.test() functions share one simulation, and rst_n
    # only clears cache state, never the backing store, so reusing an
    # address across tests would pick up residue from an earlier test's
    # writes -- correct behavior for a real backing store, but it would
    # make this test's own fresh RefModel() disagree with the DUT for a
    # reason that has nothing to do with the module's correctness.
    rng = random.Random(90210)
    addrs = [64, 72, 80, 65, 73, 81, 66, 74]  # several addresses colliding on a few indices
    for i in range(80):
        addr = rng.choice(addrs)
        we = 1 if rng.random() < 0.4 else 0
        wdata = rng.randint(0, 255)
        dut_state = await access(dut, we=we, addr=addr, wdata=wdata)
        ref_state = model.step(we, addr, wdata)
        check(i, dut_state, ref_state, "mixed-random", check_rdata=not we or ref_state["rdata"] is not None)
