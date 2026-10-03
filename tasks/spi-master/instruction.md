Fix the SPI master at `/app/repo/spi_master.v`: its per-half-bit-period counter reloads one cycle too late (`half_count == CLKS_PER_HALF_BIT` instead of `CLKS_PER_HALF_BIT - 1`), so every `sck` half-period lasts one extra system-clock cycle. The drift accumulates across the 16 edges of an 8-bit transfer, so `sck`, `mosi`, and the cycle on which `miso` is sampled all drift away from the fixed `CLKS_PER_HALF_BIT` timing a receiver expects. Read `/app/TASK_CONTRACT.md` for the exact port list and protocol before changing anything; `/app/reproduce.py` demonstrates the drift live.

## Interface

```
module spi_master #(parameter WIDTH = 8, parameter CLKS_PER_HALF_BIT = 4) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             start,
    input  wire [WIDTH-1:0] tx_data,
    input  wire             miso,
    output reg              busy,
    output reg              done,
    output reg  [WIDTH-1:0] rx_data,
    output reg              sck,
    output reg              mosi
);
```

`CLKS_PER_HALF_BIT` is fixed at `4` for grading -- do not change it. This is a fixed-mode (SPI Mode 0) master: `sck` idles low, data is transmitted and sampled MSB-first, `mosi` is valid before each rising edge, and `miso` is sampled on each rising edge of `sck`. Pulsing `start` high for one cycle while `busy` is low begins an 8-bit transfer of `tx_data`.

## Required guarantees

1. Each of the 16 `sck` edges in an 8-bit transfer (8 rising, 8 falling, strictly alternating) occurs exactly `CLKS_PER_HALF_BIT` cycles after the previous one -- no drift, no cumulative error across the transfer.
2. `mosi` presents bit `7-k` of `tx_data` (MSB-first) and is valid starting before the rising edge that corresponds to bit `k`, through just before the next rising edge.
3. `miso` is sampled on every rising edge of `sck`, in order, assembling into `rx_data` MSB-first (the first bit sampled becomes the most significant bit of `rx_data`).
4. `busy` is high for the entire transfer (from the cycle `start` is accepted through the last falling edge) and low otherwise.
5. `done` pulses high for exactly one cycle, on the same cycle `busy` drops, once all 16 edges have occurred.

## What's out of scope

Configurable CPOL/CPHA (this module is fixed to SPI Mode 0), any `WIDTH` or `CLKS_PER_HALF_BIT` other than their fixed defaults of `8` and `4`, and multiple simultaneous chip-selects.

## Deliverable

Copy the complete `spi_master.v` file to `/app/submission/spi_master.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.

## Verification

Five independent, weighted criteria, each a cocotb test running the compiled module cycle-by-cycle against an independent Python reference model (driving `miso` with a known bit sequence and checking `sck`/`mosi`/`busy`/`done`/`rx_data` every single cycle):

1. **Single-byte transfer timing.** One transfer, every `sck`/`mosi` transition checked at its exact expected cycle. (20%)
2. **`rx_data` sampling correctness.** `miso` driven with several different bit patterns, checked that `rx_data` assembles correctly. (25%)
3. **`busy`/`done` cycle-exact timing.** The total transfer length and the exact cycle `done` pulses on. (20%)
4. **Back-to-back transfers.** Several transfers issued one after another, each checked independently. (15%)
5. **A longer randomized mixed sequence** of transfers with varying `tx_data`/`miso` patterns, checked every cycle. (20%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only Icarus Verilog and cocotb are available at verification time; no network access.
