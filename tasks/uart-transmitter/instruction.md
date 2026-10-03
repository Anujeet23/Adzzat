Fix the UART transmitter at `/app/repo/uart_tx.v`: its bit-duration counter reloads one cycle too late (`clk_count == CLKS_PER_BIT` instead of `clk_count == CLKS_PER_BIT - 1`), so every bit -- the start bit, all 8 data bits, and the stop bit -- is held for `CLKS_PER_BIT + 1` cycles instead of `CLKS_PER_BIT`. The timing drifts by one extra cycle per bit, so by partway through a frame the line is no longer where a receiver sampling at the correct bit rate expects it. Read `/app/TASK_CONTRACT.md` for the exact port list and frame format before changing anything; `/app/reproduce.py` demonstrates the drift live.

## Interface

```
module uart_tx #(parameter CLKS_PER_BIT = 4) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       tx_start,
    input  wire [7:0] tx_data,
    output reg        tx_busy,
    output reg        tx,
    output reg        tx_done
);
```

`CLKS_PER_BIT` is fixed at `4` for grading -- do not change it. Pulsing `tx_start` high for exactly one cycle while `tx_busy` is low begins transmitting `tx_data`. The frame is: one start bit (`0`), eight data bits (LSB first), one stop bit (`1`), each held for exactly `CLKS_PER_BIT` clock cycles. `tx` idles high.

## Required guarantees

1. Each of the ten bits in a frame (start, 8 data, stop) is held on the `tx` line for exactly `CLKS_PER_BIT` clock cycles -- no drift, no cumulative error across the frame.
2. Data bits are transmitted least-significant-bit first.
3. `tx_busy` is high for the entire frame (from the cycle transmission begins through the last cycle of the stop bit) and low otherwise.
4. `tx_done` pulses high for exactly one cycle, on the last cycle of the stop bit, and is low every other cycle.
5. A new `tx_start` pulse issued the cycle immediately after `tx_busy` drops begins a new frame with correct timing, identical to the first -- back-to-back frames never corrupt each other's timing.

## What's out of scope

Parity bits, configurable baud/frame format, flow control, and any value of `CLKS_PER_BIT` other than its fixed default of `4`.

## Deliverable

Copy the complete `uart_tx.v` file to `/app/submission/uart_tx.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.

## Verification

Five independent, weighted criteria, each a cocotb test driving the compiled module and sampling `tx` at the exact expected midpoint of every bit slot, against an independently computed expected bit sequence:

1. **Single-byte bit timing.** One byte, every bit sampled at its exact expected cycle. (20%)
2. **`tx_busy`/`tx_done` cycle-exact timing.** The total frame length and the exact cycle `tx_done` pulses on. (25%)
3. **Back-to-back frames.** Several different bytes sent one after another, each decoded correctly. (20%)
4. **Edge-case byte patterns.** `0x00`, `0xFF`, and alternating-bit patterns. (15%)
5. **A longer randomized mixed sequence** of back-to-back bytes with idle gaps, each decoded and checked. (20%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only Icarus Verilog and cocotb are available at verification time; no network access.
