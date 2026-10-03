Fix the AXI-Lite-style write slave at `/app/repo/axi_lite_wr_slave.v`: after accepting a write, it asserts `bvalid` for exactly one cycle and then deasserts it unconditionally -- even if the master hasn't asserted `bready` yet. This violates the fundamental AXI handshake rule that a `VALID` signal must stay asserted until the corresponding `READY` is observed high in the *same* cycle; if the master stalls `bready` for even one extra cycle, the response is silently dropped. Read `/app/TASK_CONTRACT.md` for the exact port list and handshake rule before changing anything; `/app/reproduce.py` demonstrates the dropped response live.

## Interface

```
module axi_lite_wr_slave (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         awvalid,
    output reg          awready,
    input  wire [3:0]   awaddr,
    input  wire         wvalid,
    output reg          wready,
    input  wire [31:0]  wdata,
    output reg          bvalid,
    input  wire         bready,
    output wire [127:0] regs_flat
);
```

Simplified for this task: `awvalid` and `wvalid` must be asserted together in the same cycle to be accepted (independent AW/W arrival timing is out of scope). `regs_flat` is 4 concatenated 32-bit registers (`{reg3, reg2, reg1, reg0}`), exposed only so the verifier can confirm a write's effect -- it is not part of the AXI-Lite protocol itself. `awaddr[1:0]` selects one of the 4 registers.

## Required guarantees

1. `awready`/`wready` pulse high for exactly one cycle, only when `awvalid` and `wvalid` are both high, accepting the write and updating the addressed register to `wdata` that same cycle.
2. `bvalid` is asserted in the same cycle as the `awready`/`wready` pulse (all three are registered, so they become visible together, one clock edge after the request is presented).
3. **`bvalid` must not deassert while `bready` is low.** It stays asserted, unchanged, for as many cycles as the master stalls `bready` -- there is no bound on how long it may need to wait.
4. The cycle `bready` is observed high while `bvalid` is high, the transaction completes: `bvalid` deasserts the following cycle and the slave is ready to accept a new write.
5. Back-to-back writes, including ones separated by a multi-cycle `bready` stall, never corrupt a register's contents or drop a response.

## What's out of scope

Independent AW/W channel timing (they must arrive together), `BRESP` error responses (always implicitly OK), the AXI-Lite read channels, and burst transfers.

## Deliverable

Copy the complete `axi_lite_wr_slave.v` file to `/app/submission/axi_lite_wr_slave.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.

## Verification

Five independent, weighted criteria, each a cocotb test running the compiled module cycle-by-cycle against an independent Python reference model, asserting `awready`/`wready`/`bvalid`/register contents agree every single cycle:

1. **Basic write with immediate `bready`.** No stalling; the simple case. (15%)
2. **`bvalid` holds through a multi-cycle `bready` stall.** The central bug. (35%)
3. **Register persistence** across all four registers, checked via `regs_flat`. (15%)
4. **Back-to-back writes with varying stall lengths.** (15%)
5. **A longer randomized mixed sequence**, checked every cycle. (20%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only Icarus Verilog and cocotb are available at verification time; no network access.
