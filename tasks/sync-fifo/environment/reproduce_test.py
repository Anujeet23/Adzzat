"""Minimal cocotb test demonstrating the current fifo.v losing a write
issued in the same cycle as a read that frees the last slot of a full
FIFO."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

DEPTH = 8


@cocotb.test()
async def reproduce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst_n.value = 0
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()

    for i in range(DEPTH):
        dut.wr_en.value = 1
        dut.wr_data.value = i
        dut.rd_en.value = 0
        await RisingEdge(dut.clk)
        await NextTimeStep()
    print("after filling: full =", bool(dut.full.value))

    dut.wr_en.value = 1
    dut.wr_data.value = 99
    dut.rd_en.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()
    print("value read back during simultaneous op:", int(dut.rd_data.value))

    dut.wr_en.value = 0
    dut.rd_en.value = 1
    values = []
    for _ in range(DEPTH):
        await RisingEdge(dut.clk)
        await NextTimeStep()
        values.append(int(dut.rd_data.value))
    print("values drained afterward:", values)
    if 99 not in values:
        print("BUG REPRODUCED: the value written during the simultaneous "
              "full+write+read cycle was silently dropped -- it never "
              "comes back out of the FIFO.")
