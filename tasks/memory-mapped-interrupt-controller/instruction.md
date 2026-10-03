Fix the interrupt controller at `/app/repo/intr_ctrl.v`: acknowledging the currently-reported interrupt clears every sticky pending bit, not just the one being serviced -- so any other interrupt source that was also pending gets silently dropped the moment the CPU acks whichever source happened to be reported. Read `/app/TASK_CONTRACT.md` for the exact port list and semantics before changing anything; `/app/reproduce.py` demonstrates the dropped interrupt live.

## Interface

```
module intr_ctrl #(parameter N = 4) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [N-1:0] irq_in,
    input  wire [N-1:0] irq_enable,
    input  wire         ack,
    output reg           irq_out,
    output reg  [N-1:0]  pending,
    output reg  [1:0]    irq_id
);
```

`N` is fixed at `4` for grading. `pending[i]` is a sticky bit, latched on a rising edge of `irq_in[i]` and held until explicitly cleared -- it does not depend on `irq_in[i]` still being high. `irq_out` reports whether any enabled source is pending; `irq_id` is the lowest index among currently pending *and* enabled sources (lowest index wins ties). All outputs are registered, one cycle after the inputs/state they reflect.

## Required guarantees

1. A rising edge on `irq_in[i]` sets `pending[i]`, which then stays set even if `irq_in[i]` returns low, until explicitly cleared.
2. `irq_out` is high exactly when at least one bit of `pending & irq_enable` is set; `irq_id` is the lowest such index.
3. **`ack` clears only `pending[irq_id]`** -- the specific source currently being reported -- and must leave every other pending bit exactly as it was.
4. After an acknowledged source's bit clears, if another enabled source is still pending, `irq_out` remains high and `irq_id` updates to that next-lowest pending-and-enabled index.
5. A source with `irq_enable[i] = 0` is excluded from `irq_out`/`irq_id` even while `pending[i]` is set; re-enabling it later correctly reports it again if it is still pending.

## What's out of scope

Any `N` other than the fixed default of `4`, interrupt priority levels beyond simple index order, and nested/preemptive interrupt handling.

## Deliverable

Copy the complete `intr_ctrl.v` file to `/app/submission/intr_ctrl.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.

## Verification

Five independent, weighted criteria, each a cocotb test running the compiled module cycle-by-cycle against an independent Python reference model, asserting `irq_out`/`pending`/`irq_id` agree every single cycle:

1. **Sticky latching.** A pulse sets pending and it stays set after the pulse ends. (15%)
2. **Priority encoding.** Multiple pending-and-enabled sources, lowest index reported. (15%)
3. **Selective ack.** The central bug: acking one source must not clear any other pending source. (35%)
4. **Cascading acks.** After clearing the reported source, the next pending source is correctly reported. (15%)
5. **A longer randomized mixed sequence** of interrupts, enables, and acks, checked every cycle. (20%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only Icarus Verilog and cocotb are available at verification time; no network access.
