"""cocotb testbench for the fixed-Mode-0 SPI master.

Each test runs the DUT and an independent Python reference model in
lockstep, cycle by cycle, feeding the same miso sequence to both and
asserting sck/mosi/busy/done/rx_data agree after every cycle -- the
reference model is never derived from the DUT itself.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, NextTimeStep

WIDTH = 8
CLKS_PER_HALF_BIT = 4
MASK = (1 << WIDTH) - 1
NUM_EDGES = 2 * WIDTH


class RefModel:
    def __init__(self):
        self.busy = 0
        self.done = 0
        self.rx_data = 0
        self.sck = 0
        self.mosi = 0
        self.half_count = 0
        self.edge_idx = 0
        self.shift_reg = 0

    def step(self, start, tx_data, miso):
        done = 0
        if not self.busy:
            self.sck = 0
            if start:
                self.busy = 1
                self.shift_reg = tx_data & MASK
                self.mosi = (tx_data >> (WIDTH - 1)) & 1
                self.half_count = 0
                self.edge_idx = 0
        else:
            if self.half_count == CLKS_PER_HALF_BIT - 1:
                self.half_count = 0
                self.sck = 1 - self.sck
                if self.edge_idx % 2 == 0:
                    self.rx_data = ((self.rx_data << 1) | int(miso)) & MASK
                else:
                    old = self.shift_reg
                    self.mosi = (old >> (WIDTH - 2)) & 1
                    self.shift_reg = (old << 1) & MASK
                if self.edge_idx == NUM_EDGES - 1:
                    self.busy = 0
                    done = 1
                self.edge_idx += 1
            else:
                self.half_count += 1
        self.done = done
        return {
            "busy": self.busy,
            "done": self.done,
            "rx_data": self.rx_data,
            "sck": self.sck,
            "mosi": self.mosi,
        }


async def reset(dut):
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.tx_data.value = 0
    dut.miso.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await NextTimeStep()


async def cycle(dut, start=0, tx_data=0, miso=0):
    dut.start.value = start
    dut.tx_data.value = tx_data
    dut.miso.value = miso
    await RisingEdge(dut.clk)
    await NextTimeStep()
    return {
        "busy": int(dut.busy.value),
        "done": int(dut.done.value),
        "rx_data": int(dut.rx_data.value),
        "sck": int(dut.sck.value),
        "mosi": int(dut.mosi.value),
    }


def check(step_i, dut_state, ref_state, ctx):
    for key in ("busy", "done", "rx_data", "sck", "mosi"):
        assert dut_state[key] == ref_state[key], (
            "step %d (%s): %s mismatch: dut=%r ref=%r" % (step_i, ctx, key, dut_state[key], ref_state[key])
        )


async def do_transfer(dut, model, tx_data, miso_bits, ctx, margin=4):
    dut_state = await cycle(dut, start=1, tx_data=tx_data, miso=miso_bits[0] if miso_bits else 0)
    ref_state = model.step(1, tx_data, miso_bits[0] if miso_bits else 0)
    check(0, dut_state, ref_state, ctx + "-start")

    total_cycles = NUM_EDGES * CLKS_PER_HALF_BIT + margin
    bit_cursor = 0
    for i in range(total_cycles):
        miso_val = miso_bits[min(bit_cursor, len(miso_bits) - 1)] if miso_bits else 0
        dut_state = await cycle(dut, miso=miso_val)
        ref_state = model.step(0, 0, miso_val)
        check(i, dut_state, ref_state, ctx)
        bit_cursor = min(bit_cursor + 1, len(miso_bits) - 1) if miso_bits else 0


@cocotb.test()
async def test_single_transfer_timing(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()
    await do_transfer(dut, model, 0xA5, [0] * (NUM_EDGES * CLKS_PER_HALF_BIT + 4), "single")


@cocotb.test()
async def test_rx_sampling(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()
    rng = random.Random(99)
    miso_bits = [rng.randint(0, 1) for _ in range(NUM_EDGES * CLKS_PER_HALF_BIT + 4)]
    await do_transfer(dut, model, 0x3C, miso_bits, "rx-sampling")


@cocotb.test()
async def test_busy_done_timing(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()
    await do_transfer(dut, model, 0x00, [1] * (NUM_EDGES * CLKS_PER_HALF_BIT + 4), "busy-done")


@cocotb.test()
async def test_back_to_back_transfers(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()
    rng = random.Random(55)
    for i, tx in enumerate((0x11, 0x22, 0x33)):
        miso_bits = [rng.randint(0, 1) for _ in range(NUM_EDGES * CLKS_PER_HALF_BIT + 4)]
        await do_transfer(dut, model, tx, miso_bits, "b2b-%d" % i)


@cocotb.test()
async def test_mixed_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model = RefModel()
    rng = random.Random(2024)
    for i in range(6):
        tx = rng.randint(0, 255)
        miso_bits = [rng.randint(0, 1) for _ in range(NUM_EDGES * CLKS_PER_HALF_BIT + 6)]
        await do_transfer(dut, model, tx, miso_bits, "mixed-%d" % i)
