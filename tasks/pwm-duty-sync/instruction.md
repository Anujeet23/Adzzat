Fix the PWM generator at `/app/repo/pwm_gen.v` so a change to `duty` mid-period never glitches the current period's waveform. The current implementation compares the counter against the live `duty` input directly, so a write to `duty` takes effect on the very next clock edge, wherever the counter happens to be -- it must instead be latched and only take effect starting at the next period boundary, like any properly synchronized control register. Read `/app/TASK_CONTRACT.md` before changing anything; `/app/reproduce.py` demonstrates the glitch live.

## Interface

```
module pwm_gen #(parameter WIDTH = 8) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] period,
    input  wire [WIDTH-1:0] duty,
    output reg              pwm_out
);
```

An internal counter counts `0` to `period - 1` and wraps. `pwm_out` is high while the counter is less than the currently *applied* duty value, low otherwise. `period` is held constant for grading; only `duty` changes during a run. The applied duty value resets to `0`, so the first period after reset is entirely low; the `duty` input is first latched at the end of that first period.

## Required guarantees

1. With a constant `duty`, `pwm_out` is high for exactly `duty` cycles and low for exactly `period - duty` cycles, every period, indefinitely.
2. Changing `duty` while the counter is anywhere other than `0` must not affect the waveform for the remainder of the *current* period -- the period in progress finishes exactly as it would have with the old `duty`.
3. The new `duty` takes effect starting from the first cycle of the very next period (the cycle the counter returns to `0`), with no glitch, no extra short pulse, and no missing cycle at the boundary.
4. If `duty` is written more than once during the same period, only the value present at the moment the period boundary is crossed takes effect -- earlier writes within that period have no residual effect.
5. `duty = 0` (always low for the whole period) and `duty = period` (always high for the whole period) are both handled correctly as boundary cases.

## What's out of scope

Changing `period` itself during a run, and any asynchronous or combinational path from `duty` to `pwm_out` -- `pwm_out` is registered.

## Deliverable

Copy the complete `pwm_gen.v` file to `/app/submission/pwm_gen.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.

## Verification

Five independent, weighted criteria, each a cocotb test running the compiled module cycle-by-cycle against an independent Python reference model, asserting `pwm_out` agrees every single cycle:

1. **Steady-state duty cycle.** A constant `duty`, checked across several full periods. (15%)
2. **Mid-period change does not glitch the current period.** `duty` changed partway through a period, current period unaffected. (30%)
3. **New duty takes effect cleanly at the next boundary.** Checked immediately after the change takes effect. (25%)
4. **Multiple writes in one period; only the last matters.** (15%)
5. **A longer randomized mixed sequence** of duty changes at arbitrary points, checked every cycle. (15%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only Icarus Verilog and cocotb are available at verification time; no network access.
