Fix the direct-mapped cache controller at `/app/repo/dm_cache.v`: on a miss that evicts a line still holding modified ("dirty") data, it overwrites that line with the new tag and data without ever writing the old, modified data back to the backing store first -- so a write that only ever lived in the cache is silently lost the moment its line gets evicted. Read `/app/TASK_CONTRACT.md` for the exact port list and semantics before changing anything; `/app/reproduce.py` demonstrates the lost write live.

## Interface

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

A self-contained direct-mapped cache (8 lines, `INDEX_WIDTH=3`) over an internal backing store seeded with `mem[addr] == addr` at reset. Pulsing `req` for one cycle begins a read (`we=0`) or write (`we=1`) access to `addr`; `done`, `hit`, and (for reads, and for write misses) `rdata` become valid exactly one cycle later. Address bits `[INDEX_WIDTH-1:0]` select the cache line; the remaining high bits are the tag.

## Required guarantees

1. The first access to any address, on an empty cache, is a miss; `rdata` on a read miss equals the backing store's value at that address.
2. A write, hit or miss, stores `wdata` into the cache line and marks it dirty; a subsequent read of the same address is a hit returning that written value.
3. **Dirty write-back.** When a miss evicts a line that is dirty, the evicted line's data is written back to the backing store at its *own* address (reconstructed from its stored tag and the line index) before the line is overwritten with the new tag/data -- a later miss that re-fetches the evicted address must see the write-back's effect, not the original seed value.
4. Evicting a *clean* line (never written, or already written back) requires no write-back -- the backing store at that address is simply whatever it already was.
5. `hit` and `rdata` are driven only in response to `req`; with `req` low, `done` stays low and neither changes.

## What's out of scope

Any associativity other than direct-mapped, any `ADDR_WIDTH`/`INDEX_WIDTH`/`DATA_WIDTH` other than their fixed defaults of `8`/`3`/`8`, and multi-cycle backing-store latency -- the backing store responds within the same cycle.

## Deliverable

Copy the complete `dm_cache.v` file to `/app/submission/dm_cache.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.

## Verification

Five independent, weighted criteria, each a cocotb test running the compiled module against an independent Python reference model of the same cache+backing-store semantics, checked purely through the external `req`/`we`/`addr`/`wdata`/`hit`/`rdata` interface -- no internal signal is ever inspected directly:

1. **Basic hit/miss.** First access misses with the correct seeded value; repeat access hits. (15%)
2. **Write-then-read-hit.** A write followed by a same-address read returns the written value, not the stale seed. (15%)
3. **Dirty write-back on eviction.** The central bug: a dirty line's data must survive eviction and be observable when its address is later re-fetched. (35%)
4. **Clean eviction.** Evicting a never-written line requires no write-back; a later re-fetch sees the original seed value. (10%)
5. **A longer randomized mixed sequence** of reads and writes across several colliding addresses, checked against the reference model on every access. (25%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only Icarus Verilog and cocotb are available at verification time; no network access.
