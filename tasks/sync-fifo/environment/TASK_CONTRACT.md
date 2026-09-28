# Synchronous FIFO — contract

Source: an original, minimal starter at `/app/repo/fifo.v`, not a fork of an existing project.

## Interface

```verilog
module fifo #(
    parameter WIDTH = 8,
    parameter DEPTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,     // active-low, synchronous
    input  wire             wr_en,
    input  wire [WIDTH-1:0] wr_data,
    input  wire             rd_en,
    output reg  [WIDTH-1:0] rd_data,
    output wire             full,
    output wire             empty
);
```

`DEPTH` is always a power of two in graded instantiations. `rd_data` is **registered**: after a cycle where `rd_en` was asserted and the FIFO was not empty, `rd_data` holds the value that was at the front of the FIFO going into that cycle, valid starting the cycle after. `full` and `empty` are combinational functions of the FIFO's internal occupancy and reflect the occupancy resulting from whatever happened on the most recent clock edge (i.e., they already account for any read/write that just occurred).

## Required behavior

1. **Reset.** While `rst_n` is low, the FIFO synchronously clears to empty and `rd_data` resets to `0`.
2. **Plain write/read.** A write (`wr_en=1`) when not full stores `wr_data` at the back of the FIFO. A read (`rd_en=1`) when not empty removes the value at the front and presents it on `rd_data` starting the next cycle. FIFO ordering is preserved across any number of writes and reads, including pointer wraparound.
3. **Write while full, not reading.** Ignored -- no data is stored, no corruption.
4. **Read while empty, not writing.** Ignored -- `rd_data` does not change, no corruption.
5. **Simultaneous write and read while full.** The read frees a slot in the same cycle the write needs it: **the write must succeed.** Occupancy stays at `DEPTH` (one item leaves, one arrives), and the newly written value must later come back out in correct FIFO order. Rejecting this write because `full` was asserted going into the cycle, without accounting for the simultaneous read, is the specific bug this task is about.
6. **Simultaneous write and read while empty.** There is nothing to read, so the read is a no-op; the write still succeeds normally (occupancy becomes 1).

## What's out of scope

Asynchronous (dual-clock) operation, non-power-of-two depths, and any parameter values other than the ones the testbench instantiates with.

## Delivery

Your finished module must be at `/app/submission/fifo.v`, syntactically valid Verilog-2001 that Icarus Verilog can compile standalone (no other files). The verifier compiles and simulates it in a separate container from the one you worked in; it does not read `/app/repo`.
