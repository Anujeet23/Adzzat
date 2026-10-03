# AXI-Lite-style register write slave — contract

Source: an original, minimal starter at `/app/repo/axi_lite_wr_slave.v`, not a fork of an existing project.

## Port list

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

`awvalid`/`wvalid` arrive together (independent AW/W timing is out of scope). `regs_flat = {reg3, reg2, reg1, reg0}`, verification-only. `awaddr[1:0]` selects the register. `rst_n` active-low, synchronous.

## Guarantees

1. **Accept pulse.** `awready`/`wready` high for exactly one cycle when `awvalid && wvalid`; the addressed register updates to `wdata` that same cycle.
2. **Response asserts.** `bvalid` goes high in the same cycle as the `awready`/`wready` pulse (all registered, visible together one clock edge after the request).
3. **No premature deassertion.** `bvalid` never drops while `bready` is low, regardless of how many cycles that takes.
4. **Clean completion.** The cycle `bready` is high while `bvalid` is high, the transaction completes; `bvalid` drops the next cycle.
5. **No corruption across back-to-back writes**, including ones separated by multi-cycle stalls.

## What's out of scope

Independent AW/W timing, `BRESP` errors, AXI-Lite read channels, bursts.

## Delivery

Copy the complete `axi_lite_wr_slave.v` file to `/app/submission/axi_lite_wr_slave.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.
