# Button debouncer + edge detector — contract

Source: an original, minimal starter at `/app/repo/debounce.v`, not a fork of an existing project.

## Port list

```
module debounce #(parameter DEBOUNCE_CYCLES = 4) (
    input  wire clk,
    input  wire rst_n,
    input  wire btn_raw,
    output reg  btn_clean,
    output reg  btn_rise,
    output reg  btn_fall
);
```

`DEBOUNCE_CYCLES` fixed at `4` for grading. `rst_n` active-low, synchronous.

## Guarantees

1. **Stability requirement.** `btn_clean` changes only after `btn_raw` has held the new value for `DEBOUNCE_CYCLES` consecutive cycles.
2. **Timer restarts on bounce.** A change in `btn_raw` before the window completes restarts the timer against the new value.
3. **`btn_rise` from `btn_clean`.** Pulses exactly one cycle, only on a genuine `btn_clean` `0`-to-`1` transition.
4. **`btn_fall` from `btn_clean`.** Pulses exactly one cycle, only on a genuine `btn_clean` `1`-to-`0` transition.
5. **Persistent bouncing produces nothing.** No `btn_clean` change and no edge pulses while `btn_raw` keeps changing faster than `DEBOUNCE_CYCLES`.

## What's out of scope

Asynchronous reset, alternative debounce algorithms, any `DEBOUNCE_CYCLES` other than the fixed default of `4`.

## Delivery

Copy the complete `debounce.v` file to `/app/submission/debounce.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.
