"""Minimal cocotb test demonstrating the cumulative half-period drift in
the current spi_master.v."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

CLKS_PER_HALF_BIT = 4
WIDTH = 8
NUM_EDGES = 2 * WIDTH


async def reset(dut):
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.tx_data.value = 0
    dut.miso.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


@cocotb.test()
async def reproduce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    dut.start.value = 1
    dut.tx_data.value = 0xA5
    dut.miso.value = 0
    await RisingEdge(dut.clk)
    dut.start.value = 0
    await NextTimeStep()

    expected_total = NUM_EDGES * CLKS_PER_HALF_BIT
    done_cycle = None
    for i in range(expected_total + 20):
        await RisingEdge(dut.clk)
        await NextTimeStep()
        if int(dut.done.value):
            done_cycle = i
            break
    expected = expected_total - 1
    print("done pulsed at cycle offset:", done_cycle, "expected:", expected)
    if done_cycle != expected:
        print("BUG REPRODUCED: the transfer took %d cycles longer than the "
              "expected %d -- one extra cycle per half-bit-period across "
              "all 16 edges." % ((done_cycle or 0) - expected, expected))
