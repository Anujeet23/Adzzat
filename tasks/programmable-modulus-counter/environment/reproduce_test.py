"""Minimal cocotb test demonstrating the off-by-one wrap and the
load-doesn't-reset-count bugs in the current modcounter.v."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep


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


@cocotb.test()
async def reproduce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    await cycle(dut, load=1, mod_in=5)
    seen = []
    for _ in range(7):
        await cycle(dut, en=1)
        seen.append(int(dut.count.value))
    print("count sequence for modulus=5:", seen)
    if max(seen) >= 5:
        print("BUG REPRODUCED: count reached %d, but a modulus of 5 should "
              "only ever produce values 0..4." % max(seen))

    print()
    await cycle(dut, load=1, mod_in=8)
    for _ in range(5):
        await cycle(dut, en=1)
    before = int(dut.count.value)
    print("count before loading a smaller modulus:", before)
    await cycle(dut, load=1, mod_in=3)
    after = int(dut.count.value)
    print("count immediately after load:", after)
    if after != 0:
        print("BUG REPRODUCED: count=%d right after load, but load must "
              "reset count to 0 in the same cycle." % after)
