"""Minimal cocotb test demonstrating the starvation bug in the current
rr_arbiter.v: with all 4 requesters held high, grants should rotate
through all of them, but the current implementation re-grants the same
one every cycle."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep


async def reset(dut):
    dut.rst_n.value = 0
    dut.req.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


@cocotb.test()
async def reproduce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    dut.req.value = 0b1111
    granted = []
    for _ in range(8):
        await RisingEdge(dut.clk)
        await NextTimeStep()
        granted.append(int(dut.grant.value))

    print("grants over 8 cycles, all 4 requesters held high:", granted)
    distinct = set(granted)
    if len(distinct) == 1:
        print("BUG REPRODUCED: the same requester (grant=%s) was granted "
              "every single cycle -- the priority pointer never rotated "
              "past it, starving the other three requesters entirely." % bin(granted[0]))
