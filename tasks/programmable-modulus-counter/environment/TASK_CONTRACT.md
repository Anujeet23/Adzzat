# Programmable-modulus counter — contract

Source: an original, minimal starter at `/app/repo/modcounter.v`, not a fork of an existing project.

## Port list

```
module modcounter #(parameter WIDTH = 8) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             load,
    input  wire [WIDTH-1:0] mod_in,
    input  wire             en,
    output reg  [WIDTH-1:0] count,
    output reg              overflow
);
```

All signals are synchronous to `clk`, registered, active on the rising edge; `rst_n` is active-low and synchronous, forcing `count = 0`, `overflow = 0`, and `modulus = 0` while held low. The modulus most recently loaded via `load`/`mod_in` is always `>= 1` in graded inputs.

## Guarantees

1. **Increment.** While `en=1` and `load=0` and not wrapping, `count` advances by exactly 1 per cycle.
2. **Exact modulus range.** `count` takes exactly `modulus` distinct values, `0` through `modulus - 1`, before wrapping to `0`.
3. **Overflow pulse.** `overflow` is high for exactly the cycle on which `count` wraps from `modulus - 1` to `0`, and low every other cycle.
4. **Load resets count.** Asserting `load` loads `mod_in` as the new modulus and resets `count` to `0` in the same clock edge, regardless of the prior count or `en`.
5. **Pause holds count exactly.** While `en=0` and `load=0`, `count` holds its value unchanged and `overflow` is low (it is a one-cycle pulse, never held).

## What's out of scope

A modulus of `0`, runtime changes to `WIDTH`, and any asynchronous or combinational output -- `count` and `overflow` are both registered.

## Delivery

Copy the complete `modcounter.v` file to `/app/submission/modcounter.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.
