# SPI master (Mode 0, fixed) — contract

Source: an original, minimal starter at `/app/repo/spi_master.v`, not a fork of an existing project.

## Port list

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

`WIDTH=8`, `CLKS_PER_HALF_BIT=4`, fixed for grading. `rst_n` active-low, synchronous. Fixed SPI Mode 0: `sck` idles low; `mosi` set up before each rising edge; `miso` sampled on each rising edge.

## Guarantees

1. **Exact half-period timing.** Each of the 16 `sck` edges in an 8-bit transfer occurs exactly `CLKS_PER_HALF_BIT` cycles after the previous one.
2. **MOSI bit order and timing.** `mosi` presents `tx_data` MSB-first, valid before its corresponding rising edge.
3. **MISO sampling.** `miso` sampled on every rising edge, assembled MSB-first into `rx_data`.
4. **`busy` coverage.** High for the entire transfer, low otherwise.
5. **`done` pulse.** High for exactly one cycle, the same cycle `busy` drops, after all 16 edges.

## What's out of scope

Configurable CPOL/CPHA, any `WIDTH`/`CLKS_PER_HALF_BIT` other than the fixed defaults, multiple chip-selects.

## Delivery

Copy the complete `spi_master.v` file to `/app/submission/spi_master.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.
