# Direct-mapped cache controller — contract

Source: an original, minimal starter at `/app/repo/dm_cache.v`, not a fork of an existing project.

## Port list

```
module dm_cache #(parameter ADDR_WIDTH = 8, parameter INDEX_WIDTH = 3, parameter DATA_WIDTH = 8) (
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire                  req,
    input  wire                  we,
    input  wire [ADDR_WIDTH-1:0] addr,
    input  wire [DATA_WIDTH-1:0] wdata,
    output reg                   done,
    output reg                   hit,
    output reg  [DATA_WIDTH-1:0] rdata
);
```

Fixed parameters for grading: `ADDR_WIDTH=8`, `INDEX_WIDTH=3`, `DATA_WIDTH=8` (8 cache lines). An internal backing store, seeded with `mem[addr] == addr` at reset, is accessed within the same cycle (no latency). `addr[INDEX_WIDTH-1:0]` is the line index; the remaining bits are the tag. `rst_n` active-low, synchronous.

## Guarantees

1. **Cold miss, correct seed.** First access to any address misses; a read miss returns the backing store's seeded value.
2. **Write visibility.** A write (hit or miss) stores `wdata` and marks the line dirty; a later read of the same address hits with that value.
3. **Dirty write-back on eviction.** A miss that evicts a dirty line writes that line's data back to the backing store at the evicted line's own address (tag + index) before overwriting it with the new line.
4. **Clean eviction needs no write-back.** Evicting a line that was never written (or already written back) leaves the backing store at that address unchanged.
5. **Request-gated outputs.** `hit`/`rdata`/`done` only change in response to `req`; `req=0` means `done=0` and nothing else changes.

## What's out of scope

Non-direct-mapped associativity, any parameter values other than the fixed defaults, multi-cycle backing-store latency.

## Delivery

Copy the complete `dm_cache.v` file to `/app/submission/dm_cache.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.
