"""Minimal cocotb test demonstrating the dropped-interrupt bug in the
current intr_ctrl.v: acking source 0 must not clear source 2's
still-pending bit."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep


async def reset(dut):
    dut.rst_n.value = 0
    dut.irq_in.value = 0
    dut.irq_enable.value = 0b1111
    dut.ack.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


async def cycle(dut, irq_in=0, ack=0):
    dut.irq_in.value = irq_in
    dut.ack.value = ack
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return int(dut.pending.value)


@cocotb.test()
async def reproduce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    await cycle(dut, irq_in=0b0001)  # pulse source 0
    await cycle(dut, irq_in=0b0000)
    await cycle(dut, irq_in=0b0100)  # pulse source 2
    pending = await cycle(dut, irq_in=0b0000)
    print("pending before any ack:", bin(pending), "(expect sources 0 and 2 both set)")

    pending = await cycle(dut, ack=1)  # ack whichever source is currently reported (source 0, lowest index)
    pending = await cycle(dut)
    print("pending after acking source 0:", bin(pending), "(expect source 2 still pending)")
    if not (pending & 0b0100):
        print("BUG REPRODUCED: acking source 0 also cleared source 2's "
              "still-unserviced pending bit.")
