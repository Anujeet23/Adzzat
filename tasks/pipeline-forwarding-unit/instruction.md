Fix the data-hazard forwarding unit at `/app/repo/forwarding_unit.v`: when both the EX/MEM and MEM/WB pipeline stages target the same destination register as a source operand, it forwards the older MEM/WB value instead of the more recent EX/MEM value. Read `/app/TASK_CONTRACT.md` for the exact port list and priority rule before changing anything; `/app/reproduce.py` demonstrates the stale forward live.

## Interface

```
module forwarding_unit (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [4:0]  rs1,
    input  wire [4:0]  rs2,
    input  wire [4:0]  ex_mem_rd,
    input  wire        ex_mem_valid,
    input  wire [31:0] ex_mem_value,
    input  wire [4:0]  mem_wb_rd,
    input  wire        mem_wb_valid,
    input  wire [31:0] mem_wb_value,
    input  wire [31:0] regfile_rs1,
    input  wire [31:0] regfile_rs2,
    output reg  [31:0] rs1_value,
    output reg  [31:0] rs2_value
);
```

`ex_mem_valid`/`mem_wb_valid` indicate whether the instruction currently in that stage actually writes a register (a branch or store, for instance, would not). Register `5'd0` is hardwired zero and is never a hazard source, regardless of what `ex_mem_rd`/`mem_wb_rd` claim. All outputs are registered, valid one cycle after the inputs they reflect.

## Required guarantees

1. If neither stage's destination matches a source register (or the match is to register `0`), that source's value is the raw register-file read, unmodified.
2. If only the EX/MEM stage's destination matches a source register (and is nonzero, and `ex_mem_valid`), that source's value is `ex_mem_value`.
3. If only the MEM/WB stage's destination matches a source register (and is nonzero, and `mem_wb_valid`), that source's value is `mem_wb_value`.
4. If *both* stages' destinations match the same source register, `ex_mem_value` wins -- the EX/MEM hazard is strictly more recent than the MEM/WB hazard and must take priority.
5. `rs1` and `rs2` are resolved completely independently; a hazard affecting one must never influence the other.

## What's out of scope

More than two forwarding sources, a register file write port, and any combinational (same-cycle) path from inputs to outputs -- both outputs are registered.

## Deliverable

Copy the complete `forwarding_unit.v` file to `/app/submission/forwarding_unit.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.

## Verification

Five independent, weighted criteria, each a cocotb test running the compiled module cycle-by-cycle against an independent Python reference model, asserting `rs1_value`/`rs2_value` agree every single cycle:

1. **No hazard.** Neither stage matches; raw register-file values pass through. (15%)
2. **EX/MEM-only hazard.** (15%)
3. **MEM/WB-only hazard.** (15%)
4. **Both stages match the same register -- EX/MEM must win.** The central bug. (35%)
5. **A longer randomized mixed sequence** of hazard combinations across both `rs1` and `rs2` independently, checked every cycle. (20%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only Icarus Verilog and cocotb are available at verification time; no network access.
