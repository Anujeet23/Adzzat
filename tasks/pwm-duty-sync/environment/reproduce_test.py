"""Minimal cocotb test demonstrating the mid-period duty-change glitch in
the current pwm_gen.v."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

PERIOD = 10


async def reset(dut):
    dut.rst_n.value = 0
    dut.period.value = PERIOD
    dut.duty.value = 3
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


@cocotb.test()
async def reproduce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    dut.period.value = PERIOD
    dut.duty.value = 3
    trace = []
    for i in range(PERIOD):
        if i == 5:
            dut.duty.value = 8  # change mid-period, should not affect this period
        await RisingEdge(dut.clk)
        await NextTimeStep()
        trace.append(int(dut.pwm_out.value))

    expected_unaffected = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
    print("trace for this period:", trace)
    print("expected (old duty=3, unaffected by mid-period change):", expected_unaffected)
    if trace != expected_unaffected:
        print("BUG REPRODUCED: the mid-period write to duty=8 changed this "
              "period's waveform instead of waiting for the next period "
              "boundary.")
