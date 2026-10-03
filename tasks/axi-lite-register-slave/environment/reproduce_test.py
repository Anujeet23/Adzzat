"""Minimal cocotb test demonstrating the dropped-response bug in the
current axi_lite_wr_slave.v: holding bready low for a couple of cycles
after a write should not cause bvalid to drop before bready arrives."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep


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


@cocotb.test()
async def reproduce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    dut.awvalid.value = 1
    dut.awaddr.value = 0
    dut.wvalid.value = 1
    dut.wdata.value = 0x1234
    dut.bready.value = 0
    await RisingEdge(dut.clk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await NextTimeStep()

    bvalid_trace = []
    for i in range(4):
        await RisingEdge(dut.clk)
        await NextTimeStep()
        bvalid_trace.append(int(dut.bvalid.value))
        if i == 2:
            dut.bready.value = 1

    print("bvalid over 4 cycles with bready held low for 3 cycles then raised:", bvalid_trace)
    if bvalid_trace[1] == 0:
        print("BUG REPRODUCED: bvalid dropped to 0 at cycle 1, before bready "
              "was ever observed high -- the response was silently lost.")
