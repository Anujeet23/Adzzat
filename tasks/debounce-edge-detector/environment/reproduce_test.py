"""Minimal cocotb test demonstrating the non-restarting debounce timer and
the raw-derived edge pulses in the current debounce.v."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep


async def reset(dut):
    dut.rst_n.value = 0
    dut.btn_raw.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await NextTimeStep()


async def cycle(dut, btn_raw):
    dut.btn_raw.value = btn_raw
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return {"btn_clean": int(dut.btn_clean.value), "btn_rise": int(dut.btn_rise.value)}


@cocotb.test()
async def reproduce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    # bounce: raw goes 1, then 0 again before the 4-cycle window completes,
    # then stays 0. btn_clean must never become 1.
    seq = [1, 1, 0, 0, 0, 0, 0, 0]
    saw_rise = False
    final_clean = None
    for v in seq:
        state = await cycle(dut, v)
        if state["btn_rise"]:
            saw_rise = True
        final_clean = state["btn_clean"]
    print("final btn_clean:", final_clean, "saw btn_rise during bounce:", saw_rise)
    if final_clean == 1 or saw_rise:
        print("BUG REPRODUCED: the debounce timer locked in the first "
              "sampled value (1) instead of restarting when btn_raw "
              "bounced back to 0, and/or pulsed btn_rise on the raw "
              "toggle instead of waiting for a genuine btn_clean "
              "transition.")
