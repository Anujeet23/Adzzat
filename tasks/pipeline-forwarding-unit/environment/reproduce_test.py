"""Minimal cocotb test demonstrating the inverted forwarding priority in
the current forwarding_unit.v: when both EX/MEM and MEM/WB target
register rs1, the more recent EX/MEM value must win."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep


async def reset(dut):
    dut.rst_n.value = 0
    for sig in ("rs1", "rs2", "ex_mem_rd", "ex_mem_valid", "ex_mem_value",
                "mem_wb_rd", "mem_wb_valid", "mem_wb_value", "regfile_rs1", "regfile_rs2"):
        getattr(dut, sig).value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


@cocotb.test()
async def reproduce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    dut.rs1.value = 7
    dut.ex_mem_rd.value = 7
    dut.ex_mem_valid.value = 1
    dut.ex_mem_value.value = 0xAAAA
    dut.mem_wb_rd.value = 7
    dut.mem_wb_valid.value = 1
    dut.mem_wb_value.value = 0xBBBB
    dut.regfile_rs1.value = 0xCCCC

    await RisingEdge(dut.clk)
    await NextTimeStep()

    got = int(dut.rs1_value.value)
    print("rs1_value with both EX/MEM and MEM/WB targeting rs1:", hex(got))
    print("expected EX/MEM value (more recent):", hex(0xAAAA))
    if got != 0xAAAA:
        print("BUG REPRODUCED: got %s instead of the more recent EX/MEM "
              "value 0xaaaa -- MEM/WB's stale value was forwarded instead." % hex(got))
