# Interrupt controller — contract

Source: an original, minimal starter at `/app/repo/intr_ctrl.v`, not a fork of an existing project.

## Port list

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

`N=4`, fixed for grading. `rst_n` active-low, synchronous. Outputs registered, one cycle after the inputs/state they reflect.

## Guarantees

1. **Sticky pending.** A rising edge on `irq_in[i]` sets `pending[i]`; it remains set regardless of `irq_in[i]`'s later level, until cleared.
2. **Priority encoding.** `irq_out = |(pending & irq_enable)`; `irq_id` is the lowest set index of `pending & irq_enable`.
3. **Selective ack.** `ack` clears only `pending[irq_id]`; every other pending bit is untouched.
4. **Cascading.** Clearing the reported source reveals the next-lowest pending-and-enabled source, if any.
5. **Enable gating.** A disabled source never affects `irq_out`/`irq_id`, regardless of its pending state.

## What's out of scope

Any `N` other than `4`, multi-level priority, nested/preemptive interrupts.

## Delivery

Copy the complete `intr_ctrl.v` file to `/app/submission/intr_ctrl.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.
