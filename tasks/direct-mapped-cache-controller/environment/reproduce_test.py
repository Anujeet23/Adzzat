"""Minimal cocotb test demonstrating the lost dirty write-back in the
current dm_cache.v: a written value, once evicted, must still be
observable through a later re-fetch -- entirely through the external
interface, never by inspecting internal signals."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

ADDR_A = 16  # index 0, tag 2
ADDR_B = 24  # index 0, tag 3 -- same line as A, different tag


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


@cocotb.test()
async def reproduce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    await access(dut, we=1, addr=ADDR_A, wdata=0x5A)  # miss, writes 0x5A, marks dirty
    await access(dut, we=0, addr=ADDR_B)  # miss, evicts A's dirty line
    result = await access(dut, we=0, addr=ADDR_A)  # miss again, re-fetches A from backing store

    print("re-fetched addr A after eviction:", hex(result["rdata"]), "expected: 0x5a")
    if result["rdata"] != 0x5A:
        print("BUG REPRODUCED: the write of 0x5a to address %d was lost when "
              "its line was evicted -- the backing store still has the "
              "original seed value instead of the write-back." % ADDR_A)
