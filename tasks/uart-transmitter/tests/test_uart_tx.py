"""cocotb testbench for the UART transmitter.

Each test drives the DUT, samples `tx` at the exact midpoint of every
expected bit slot (per the fixed CLKS_PER_BIT=4 timing), and compares
against an independently computed expected bit sequence -- never derived
from the DUT itself.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

CLKS_PER_BIT = 4
NUM_BITS = 10  # start + 8 data + stop
FRAME_CYCLES = NUM_BITS * CLKS_PER_BIT


def expected_bits(byte_val):
    bits = [0]
    for i in range(8):
        bits.append((byte_val >> i) & 1)
    bits.append(1)
    return bits


async def reset(dut):
    dut.rst_n.value = 0
    dut.tx_start.value = 0
    dut.tx_data.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


async def step(dut, tx_start=0, tx_data=0):
    dut.tx_start.value = tx_start
    dut.tx_data.value = tx_data
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return {
        "tx": int(dut.tx.value),
        "tx_busy": int(dut.tx_busy.value),
        "tx_done": int(dut.tx_done.value),
    }


async def send_byte(dut, byte_val, margin=6):
    """Pulses tx_start, then samples tx at the midpoint of every expected
    bit slot and tracks tx_busy/tx_done. Returns (sampled_bits,
    busy_trace, done_offset)."""
    await step(dut, tx_start=1, tx_data=byte_val)
    sampled = [None] * NUM_BITS
    busy_trace = []
    done_offset = None
    for cycle_i in range(FRAME_CYCLES + margin):
        state = await step(dut)
        busy_trace.append(state["tx_busy"])
        for bit_i in range(NUM_BITS):
            mid = bit_i * CLKS_PER_BIT + CLKS_PER_BIT // 2
            if cycle_i == mid:
                sampled[bit_i] = state["tx"]
        if state["tx_done"] and done_offset is None:
            done_offset = cycle_i
    return sampled, busy_trace, done_offset


async def wait_idle(dut, max_cycles=FRAME_CYCLES + 10):
    for _ in range(max_cycles):
        state = await step(dut)
        if not state["tx_busy"]:
            return
    raise AssertionError("tx_busy never dropped within %d cycles" % max_cycles)


@cocotb.test()
async def test_single_byte_timing(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    sampled, _, _ = await send_byte(dut, 0xA5)
    assert sampled == expected_bits(0xA5), (
        "sampled bits %r do not match expected %r for byte 0xA5" % (sampled, expected_bits(0xA5))
    )


@cocotb.test()
async def test_busy_done_timing(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    sampled, busy_trace, done_offset = await send_byte(dut, 0x3C)
    assert sampled == expected_bits(0x3C), "bit pattern mismatch for 0x3C: %r" % sampled

    expected_done = FRAME_CYCLES - 1
    assert done_offset == expected_done, (
        "tx_done pulsed at cycle %r, expected exactly %d" % (done_offset, expected_done)
    )
    assert all(busy_trace[: FRAME_CYCLES - 1]), (
        "tx_busy must stay high for the %d cycles before the frame completes" % (FRAME_CYCLES - 1)
    )
    assert not any(busy_trace[FRAME_CYCLES - 1 :]), "tx_busy must drop on the same cycle tx_done pulses"


@cocotb.test()
async def test_back_to_back_frames(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    # margin=0 ends each call on the cycle tx_busy drops, so the next frame's
    # tx_start is issued on the very next cycle (guarantee 5).
    for byte_val in (0x11, 0x22, 0x33):
        sampled, _, _ = await send_byte(dut, byte_val, margin=0)
        assert sampled == expected_bits(byte_val), (
            "back-to-back byte 0x%02X: sampled %r != expected %r" % (byte_val, sampled, expected_bits(byte_val))
        )


@cocotb.test()
async def test_edge_case_patterns(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    for byte_val in (0x00, 0xFF, 0x01, 0x80, 0x55, 0xAA):
        sampled, _, _ = await send_byte(dut, byte_val)
        assert sampled == expected_bits(byte_val), (
            "byte 0x%02X: sampled %r != expected %r" % (byte_val, sampled, expected_bits(byte_val))
        )


@cocotb.test()
async def test_mixed_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    rng = random.Random(777)
    for i in range(8):
        byte_val = rng.randint(0, 255)
        sampled, _, _ = await send_byte(dut, byte_val)
        assert sampled == expected_bits(byte_val), (
            "mixed step %d, byte 0x%02X: sampled %r != expected %r"
            % (i, byte_val, sampled, expected_bits(byte_val))
        )
        if rng.random() < 0.5:
            for _ in range(rng.randint(1, 3)):
                await step(dut)
