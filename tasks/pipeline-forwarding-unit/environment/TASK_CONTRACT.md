# Pipeline data-hazard forwarding unit — contract

Source: an original, minimal starter at `/app/repo/forwarding_unit.v`, not a fork of an existing project.

## Port list

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

`rst_n` active-low, synchronous. Register `5'd0` is never a hazard source. Outputs are registered, one cycle after their inputs.

## Guarantees

1. **No hazard.** Neither stage's destination matches (or the match is to register 0) -> raw register-file value.
2. **EX/MEM-only hazard.** -> `ex_mem_value`.
3. **MEM/WB-only hazard.** -> `mem_wb_value`.
4. **Both stages match.** `ex_mem_value` wins -- it is the more recent hazard.
5. **Independence.** `rs1` and `rs2` resolve independently of each other.

## What's out of scope

More than two forwarding sources, a register file write port, any combinational input-to-output path.

## Delivery

Copy the complete `forwarding_unit.v` file to `/app/submission/forwarding_unit.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.
