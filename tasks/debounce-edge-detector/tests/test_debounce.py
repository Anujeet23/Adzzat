"""cocotb testbench for the button debouncer + edge detector.

Each test runs the DUT and an independent Python reference model in
lockstep, cycle by cycle, feeding the same btn_raw sequence to both and
asserting btn_clean/btn_rise/btn_fall agree every cycle -- the reference
model is never derived from the DUT itself.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

DEBOUNCE_CYCLES = 4


class RefModel:
    def __init__(self, debounce_cycles):
        self.dc = debounce_cycles
        self.btn_clean = 0
        self.count = 0
        self.candidate = 0
        self.counting = 0

    def step(self, btn_raw):
        btn_raw = int(btn_raw)
        btn_rise = 0
        btn_fall = 0
        if not self.counting:
            if btn_raw != self.btn_clean:
                self.counting = 1
                self.candidate = btn_raw
                self.count = 1
        else:
            if btn_raw != self.candidate:
                self.candidate = btn_raw
                self.count = 1
                if btn_raw == self.btn_clean:
                    self.counting = 0
            elif self.count == self.dc - 1:
                old_clean = self.btn_clean
                self.btn_clean = self.candidate
                self.counting = 0
                if self.candidate and not old_clean:
                    btn_rise = 1
                if (not self.candidate) and old_clean:
                    btn_fall = 1
            else:
                self.count += 1
        return {"btn_clean": self.btn_clean, "btn_rise": btn_rise, "btn_fall": btn_fall}


async def reset(dut):
    dut.rst_n.value = 0
    dut.btn_raw.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


async def cycle(dut, btn_raw):
    dut.btn_raw.value = btn_raw
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return {
        "btn_clean": int(dut.btn_clean.value),
        "btn_rise": int(dut.btn_rise.value),
        "btn_fall": int(dut.btn_fall.value),
    }


def check(step_i, dut_state, ref_state, ctx):
    for key in ("btn_clean", "btn_rise", "btn_fall"):
        assert dut_state[key] == ref_state[key], (
            "step %d (%s): %s mismatch: dut=%r ref=%r" % (step_i, ctx, key, dut_state[key], ref_state[key])
        )


@cocotb.test()
async def test_basic_debounce(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(DEBOUNCE_CYCLES)

    seq = [1] * 10
    for i, v in enumerate(seq):
        dut_state = await cycle(dut, v)
        ref_state = model.step(v)
        check(i, dut_state, ref_state, "basic")
    assert model.btn_clean == 1, "reference model itself should have settled -- test bug if this fails"


@cocotb.test()
async def test_bounce_restarts_timer(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(DEBOUNCE_CYCLES)

    # bounces: 1,1 (2 cycles, short of the 4-cycle window), then back to 0
    # and finally settles on 1. The final decision must reflect the LAST
    # stable run (1), and must take DEBOUNCE_CYCLES from the LAST change.
    seq = [1, 1, 0, 1, 1, 1, 1, 1, 1]
    for i, v in enumerate(seq):
        dut_state = await cycle(dut, v)
        ref_state = model.step(v)
        check(i, dut_state, ref_state, "bounce-restart")


@cocotb.test()
async def test_edges_follow_clean_not_raw(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(DEBOUNCE_CYCLES)

    # rapid bouncing, never stable for DEBOUNCE_CYCLES -- btn_clean must
    # never change and no edge must ever pulse.
    rng = random.Random(7)
    seq = [rng.randint(0, 1) for _ in range(30)]
    for i, v in enumerate(seq):
        dut_state = await cycle(dut, v)
        ref_state = model.step(v)
        check(i, dut_state, ref_state, "rapid-bounce")
        assert dut_state["btn_clean"] == 0, "step %d: btn_clean must never leave 0 under persistent bouncing" % i
        assert not dut_state["btn_rise"] and not dut_state["btn_fall"], (
            "step %d: no edge pulse is allowed while btn_clean never changes" % i
        )


@cocotb.test()
async def test_repeated_transitions(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(DEBOUNCE_CYCLES)

    seq = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    for i, v in enumerate(seq):
        dut_state = await cycle(dut, v)
        ref_state = model.step(v)
        check(i, dut_state, ref_state, "repeated")


@cocotb.test()
async def test_mixed_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel(DEBOUNCE_CYCLES)

    rng = random.Random(31415)
    level = 0
    for i in range(120):
        if rng.random() < 0.3:
            level = 1 - level
        v = level if rng.random() < 0.8 else 1 - level
        dut_state = await cycle(dut, v)
        ref_state = model.step(v)
        check(i, dut_state, ref_state, "mixed-random")
