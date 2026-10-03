# PWM generator with glitch-free duty sync — contract

Source: an original, minimal starter at `/app/repo/pwm_gen.v`, not a fork of an existing project.

## Port list

```
module pwm_gen #(parameter WIDTH = 8) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] period,
    input  wire [WIDTH-1:0] duty,
    output reg              pwm_out
);
```

`rst_n` active-low, synchronous. An internal counter counts `0` to `period - 1` and wraps to `0`. `period` is held constant for grading. The applied duty value resets to `0` (the first period after reset is entirely low); `duty` is first latched at the end of that first period.

## Guarantees

1. **Steady state.** With constant `duty`, `pwm_out` is high for exactly `duty` cycles and low for exactly `period - duty` cycles, every period.
2. **No mid-period glitch.** A write to `duty` while the counter is not `0` does not affect the waveform for the remainder of the current period.
3. **Clean boundary application.** The new `duty` takes effect starting the first cycle of the next period, with no glitch or missing cycle.
4. **Last-write-wins within a period.** Multiple writes to `duty` within one period: only the value present at the period boundary takes effect.
5. **Boundary duty values.** `duty = 0` and `duty = period` are both handled correctly.

## What's out of scope

Changing `period` during a run; any combinational path from `duty` to `pwm_out`.

## Delivery

Copy the complete `pwm_gen.v` file to `/app/submission/pwm_gen.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.
