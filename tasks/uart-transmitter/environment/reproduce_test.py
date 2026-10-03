"""Minimal cocotb test demonstrating the cumulative bit-timing drift in
the current uart_tx.v."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

CLKS_PER_BIT = 4


async def reset(dut):
    dut.rst_n.value = 0
    dut.tx_start.value = 0
    dut.tx_data.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


@cocotb.test()
async def reproduce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    dut.tx_start.value = 1
    dut.tx_data.value = 0xA5
    await RisingEdge(dut.clk)
    dut.tx_start.value = 0
    await NextTimeStep()

    total_cycles = 10 * CLKS_PER_BIT
    done_cycle = None
    for i in range(total_cycles + 10):
        await RisingEdge(dut.clk)
        await NextTimeStep()
        if int(dut.tx_done.value):
            done_cycle = i
            break
    expected = total_cycles - 1
    print("tx_done pulsed at cycle offset:", done_cycle, "expected:", expected)
    if done_cycle != expected:
        print("BUG REPRODUCED: the frame took %d cycles longer than the "
              "expected %d, one extra cycle per bit across the 10-bit "
              "frame -- the bit-duration counter reloads one cycle too "
              "late." % ((done_cycle or 0) - expected, expected))
