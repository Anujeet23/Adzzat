"""cocotb testbench for the glitch-free PWM generator.

Each test runs the DUT and an independent Python reference model in
lockstep, cycle by cycle, feeding the same `duty` input to both and
asserting pwm_out agrees every cycle -- the reference model is never
derived from the DUT itself.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

PERIOD = 10


class RefModel:
    def __init__(self, period):
        self.period = period
        self.counter = 0
        self.duty_reg = 0

    def step(self, duty):
        pwm_out = 1 if self.counter < self.duty_reg else 0
        if self.counter == self.period - 1:
            self.counter = 0
            self.duty_reg = duty
        else:
            self.counter += 1
        return {"pwm_out": pwm_out}


async def reset(dut, period, initial_duty):
    # pwm_gen's counter free-runs every cycle once out of reset (there is no
    # start/enable gate), so -- unlike the other RTL tasks' reset helpers --
    # this must NOT take an extra post-reset edge, or the counter advances
    # before the test loop's first cycle() call, misaligning it from the
    # reference model's initial state.
    dut.rst_n.value = 0
    dut.period.value = period
    dut.duty.value = initial_duty
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await NextTimeStep()


async def cycle(dut, duty):
    dut.duty.value = duty
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return {"pwm_out": int(dut.pwm_out.value)}


def check(step_i, dut_state, ref_state, ctx):
    assert dut_state["pwm_out"] == ref_state["pwm_out"], (
        "step %d (%s): pwm_out mismatch: dut=%r ref=%r" % (step_i, ctx, dut_state["pwm_out"], ref_state["pwm_out"])
    )


@cocotb.test()
async def test_steady_state(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut, PERIOD, 4)
    model = RefModel(PERIOD)

    for i in range(4 * PERIOD):
        dut_state = await cycle(dut, 4)
        ref_state = model.step(4)
        check(i, dut_state, ref_state, "steady")


@cocotb.test()
async def test_mid_period_no_glitch(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut, PERIOD, 3)
    model = RefModel(PERIOD)

    # duty_reg resets to 0, independent of the `duty` input, and only
    # latches a real value at the first period boundary -- so warm up
    # for one full period first to get duty_reg=3 latched in.
    for i in range(PERIOD):
        dut_state = await cycle(dut, 3)
        ref_state = model.step(3)
        check(i, dut_state, ref_state, "warmup")

    # second period: change duty to 8 mid-period; this whole period must
    # still reflect the old duty=3, unaffected by the change.
    for i in range(PERIOD):
        duty = 8 if i >= 5 else 3
        dut_state = await cycle(dut, duty)
        ref_state = model.step(duty)
        check(i, dut_state, ref_state, "mid-period-change")
        assert dut_state["pwm_out"] == (1 if i < 3 else 0), (
            "step %d: pwm_out must still reflect the old duty=3 for this entire period, got %r"
            % (i, dut_state["pwm_out"])
        )


@cocotb.test()
async def test_clean_boundary_application(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut, PERIOD, 3)
    model = RefModel(PERIOD)

    for i in range(PERIOD):
        dut_state = await cycle(dut, 3)
        ref_state = model.step(3)
        check(i, dut_state, ref_state, "warmup")

    for i in range(PERIOD):
        duty = 8 if i >= 5 else 3
        dut_state = await cycle(dut, duty)
        ref_state = model.step(duty)
        check(i, dut_state, ref_state, "pre-boundary")

    for i in range(PERIOD):
        dut_state = await cycle(dut, 8)
        ref_state = model.step(8)
        check(i, dut_state, ref_state, "post-boundary")
        assert dut_state["pwm_out"] == (1 if i < 8 else 0), (
            "step %d of the new period: expected duty=8's waveform, got pwm_out=%r" % (i, dut_state["pwm_out"])
        )


@cocotb.test()
async def test_multiple_writes_last_wins(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut, PERIOD, 2)
    model = RefModel(PERIOD)

    duty_schedule = [2, 2, 5, 5, 7, 7, 1, 1, 1, 9]  # several writes within one period; last value (9) wins
    for i, duty in enumerate(duty_schedule):
        dut_state = await cycle(dut, duty)
        ref_state = model.step(duty)
        check(i, dut_state, ref_state, "multi-write")

    for i in range(PERIOD):
        dut_state = await cycle(dut, 9)
        ref_state = model.step(9)
        check(i, dut_state, ref_state, "after-multi-write")
        assert dut_state["pwm_out"] == (1 if i < 9 else 0), (
            "step %d: expected only the last write (duty=9) to have taken effect" % i
        )


@cocotb.test()
async def test_mixed_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut, PERIOD, 0)
    model = RefModel(PERIOD)

    rng = random.Random(31337)
    duty = 0
    for i in range(10 * PERIOD):
        if rng.random() < 0.15:
            duty = rng.choice([0, PERIOD] + list(range(1, PERIOD)))
        dut_state = await cycle(dut, duty)
        ref_state = model.step(duty)
        check(i, dut_state, ref_state, "mixed-random")
