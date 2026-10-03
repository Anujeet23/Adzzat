"""cocotb testbench for the data-hazard forwarding unit.

Each test runs the DUT and an independent Python reference model in
lockstep, cycle by cycle, asserting rs1_value/rs2_value agree every
cycle -- the reference model is never derived from the DUT itself.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep


def resolve(rs, ex_rd, ex_valid, ex_val, wb_rd, wb_valid, wb_val, regval):
    if ex_valid and ex_rd != 0 and ex_rd == rs:
        return ex_val
    if wb_valid and wb_rd != 0 and wb_rd == rs:
        return wb_val
    return regval


def model_step(inputs):
    rs1_value = resolve(
        inputs["rs1"], inputs["ex_mem_rd"], inputs["ex_mem_valid"], inputs["ex_mem_value"],
        inputs["mem_wb_rd"], inputs["mem_wb_valid"], inputs["mem_wb_value"], inputs["regfile_rs1"],
    )
    rs2_value = resolve(
        inputs["rs2"], inputs["ex_mem_rd"], inputs["ex_mem_valid"], inputs["ex_mem_value"],
        inputs["mem_wb_rd"], inputs["mem_wb_valid"], inputs["mem_wb_value"], inputs["regfile_rs2"],
    )
    return {"rs1_value": rs1_value, "rs2_value": rs2_value}


FIELDS = (
    "rs1", "rs2", "ex_mem_rd", "ex_mem_valid", "ex_mem_value",
    "mem_wb_rd", "mem_wb_valid", "mem_wb_value", "regfile_rs1", "regfile_rs2",
)


async def reset(dut):
    dut.rst_n.value = 0
    for f in FIELDS:
        getattr(dut, f).value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


async def cycle(dut, inputs):
    for f in FIELDS:
        getattr(dut, f).value = inputs[f]
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return {"rs1_value": int(dut.rs1_value.value), "rs2_value": int(dut.rs2_value.value)}


def check(step_i, dut_state, ref_state, ctx):
    for key in ("rs1_value", "rs2_value"):
        assert dut_state[key] == ref_state[key], (
            "step %d (%s): %s mismatch: dut=%#x ref=%#x" % (step_i, ctx, key, dut_state[key], ref_state[key])
        )


def base_inputs():
    return {f: 0 for f in FIELDS}


@cocotb.test()
async def test_no_hazard(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    cases = []
    inp = base_inputs()
    inp.update(rs1=3, rs2=5, regfile_rs1=0x1111, regfile_rs2=0x2222)
    cases.append(dict(inp))
    inp = base_inputs()
    inp.update(rs1=0, rs2=0, ex_mem_rd=0, ex_mem_valid=1, ex_mem_value=0x9999,
               mem_wb_rd=0, mem_wb_valid=1, mem_wb_value=0x8888, regfile_rs1=0, regfile_rs2=0)
    cases.append(dict(inp))

    for i, c in enumerate(cases):
        dut_state = await cycle(dut, c)
        ref_state = model_step(c)
        check(i, dut_state, ref_state, "no-hazard")


@cocotb.test()
async def test_ex_mem_only(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    inp = base_inputs()
    inp.update(rs1=9, rs2=12, ex_mem_rd=9, ex_mem_valid=1, ex_mem_value=0xAAAA,
               mem_wb_rd=0, mem_wb_valid=0, mem_wb_value=0, regfile_rs1=0x1234, regfile_rs2=0x5678)
    dut_state = await cycle(dut, inp)
    ref_state = model_step(inp)
    check(0, dut_state, ref_state, "ex-mem-only")
    assert dut_state["rs1_value"] == 0xAAAA


@cocotb.test()
async def test_mem_wb_only(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    inp = base_inputs()
    inp.update(rs1=9, rs2=12, ex_mem_rd=0, ex_mem_valid=0, ex_mem_value=0,
               mem_wb_rd=12, mem_wb_valid=1, mem_wb_value=0xBBBB, regfile_rs1=0x1234, regfile_rs2=0x5678)
    dut_state = await cycle(dut, inp)
    ref_state = model_step(inp)
    check(0, dut_state, ref_state, "mem-wb-only")
    assert dut_state["rs2_value"] == 0xBBBB


@cocotb.test()
async def test_both_hazards_ex_mem_wins(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    inp = base_inputs()
    inp.update(rs1=7, rs2=7, ex_mem_rd=7, ex_mem_valid=1, ex_mem_value=0xAAAA,
               mem_wb_rd=7, mem_wb_valid=1, mem_wb_value=0xBBBB, regfile_rs1=0xCCCC, regfile_rs2=0xCCCC)
    dut_state = await cycle(dut, inp)
    ref_state = model_step(inp)
    check(0, dut_state, ref_state, "both-hazards")
    assert dut_state["rs1_value"] == 0xAAAA, "EX/MEM must win when both stages target the same register"
    assert dut_state["rs2_value"] == 0xAAAA, "EX/MEM must win for rs2 too"


@cocotb.test()
async def test_mixed_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    rng = random.Random(13579)
    for i in range(150):
        inp = base_inputs()
        inp["rs1"] = rng.randint(0, 6)
        inp["rs2"] = rng.randint(0, 6)
        inp["ex_mem_rd"] = rng.randint(0, 6)
        inp["ex_mem_valid"] = rng.randint(0, 1)
        inp["ex_mem_value"] = rng.randint(0, 0xFFFFFFFF)
        inp["mem_wb_rd"] = rng.randint(0, 6)
        inp["mem_wb_valid"] = rng.randint(0, 1)
        inp["mem_wb_value"] = rng.randint(0, 0xFFFFFFFF)
        inp["regfile_rs1"] = rng.randint(0, 0xFFFFFFFF)
        inp["regfile_rs2"] = rng.randint(0, 0xFFFFFFFF)
        dut_state = await cycle(dut, inp)
        ref_state = model_step(inp)
        check(i, dut_state, ref_state, "mixed-random")
