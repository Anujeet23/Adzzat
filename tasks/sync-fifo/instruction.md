Fix the synchronous FIFO at `/app/repo/fifo.v` so a write issued in the same clock cycle as a read that frees the last slot of a full FIFO succeeds instead of being silently dropped. Read `/app/TASK_CONTRACT.md` for the exact interface and required behavior before changing anything; running `python3 /app/reproduce.py` compiles and simulates the current module and prints the dropped value never coming back out.

## Interface

```verilog
module fifo #(parameter WIDTH = 8, parameter DEPTH = 8) (
    input  wire clk, input wire rst_n,
    input  wire wr_en, input wire [WIDTH-1:0] wr_data,
    input  wire rd_en, output reg [WIDTH-1:0] rd_data,
    output wire full, output wire empty
);
```

`DEPTH` is always a power of two. `rd_data` is registered: after a cycle where `rd_en` was asserted and the FIFO wasn't empty, the value at the old front of the FIFO appears on `rd_data` starting the next cycle. `full`/`empty` reflect occupancy after whatever just happened on the most recent edge.

## Required behavior

Reset (`rst_n` low) synchronously clears the FIFO. A write when not full stores `wr_data`; a read when not empty pops the front value onto `rd_data`; FIFO order is preserved across any number of operations, including pointer wraparound. A write while full with no simultaneous read is correctly ignored, and a read while empty with no simultaneous write is correctly ignored -- the current module already gets both of those right. The bug is specifically the simultaneous case: when the FIFO is full and both `wr_en` and `rd_en` are asserted in the same cycle, the read frees a slot that the write needs, **and the write must succeed** -- occupancy stays at `DEPTH`, and the newly written value must come back out later in correct order. A write+read at empty must also work correctly (the read is a no-op, the write still succeeds).

## Deliverable

Your finished module must be at `/app/submission/fifo.v`, syntactically valid Verilog-2001 that Icarus Verilog can compile standalone with no other files. The verifier compiles and simulates it in a separate container from the one you worked in; it does not read `/app/repo`.

## Verification

Five independent, weighted cocotb/Icarus-Verilog simulation checks, each comparing the module's cycle-by-cycle behavior against an independent Python reference model, not source inspection: basic in-order write/read (15%); full and empty flags asserting at exactly the right occupancy (20%); FIFO ordering across 120 randomized operations stressing pointer wraparound (20%); the simultaneous full+write+read case across all `DEPTH` slots, then a full drain confirming every written value comes back in order (30%); and the simultaneous empty+write+read case (15%). A full pass requires all five; per-check outcomes are retained separately for diagnosis.
