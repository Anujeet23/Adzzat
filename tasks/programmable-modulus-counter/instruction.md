Fix the programmable-modulus counter at `/app/repo/modcounter.v`: it counts one value too many before wrapping (`0..modulus` instead of `0..modulus-1`, so a modulus of 5 produces 6 distinct values), and loading a new modulus does not reset the current count, so a stale count can sit outside the valid range of the new modulus. Read `/app/TASK_CONTRACT.md` for the exact port list and timing before changing anything; `/app/reproduce.py` demonstrates both bugs live in simulation.

## Interface

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

All signals are synchronous to `clk`, registered, active on the rising edge; `rst_n` is active-low and synchronous. `modulus` (the value most recently loaded via `load`/`mod_in`) is always `>= 1` in graded inputs.

## Required guarantees

1. While enabled (`en=1`, `load=0`) and not wrapping, `count` increments by exactly 1 each cycle.
2. `count` must cycle through exactly `modulus` distinct values, `0` to `modulus - 1`, before wrapping back to `0` -- never `modulus` values, never `modulus - 2`.
3. `overflow` pulses high for exactly the one cycle on which `count` wraps from `modulus - 1` back to `0`, and is low every other cycle.
4. Asserting `load` (regardless of `en`) loads `mod_in` as the new modulus **and** resets `count` to `0` in that same clock edge -- the counter never continues from a stale count under a new modulus.
5. While `en=0` and `load=0`, `count` holds its current value exactly and `overflow` is low (it is a one-cycle pulse, never held) -- counting pauses completely and resumes from where it left off once `en` returns high.

## What's out of scope

A modulus of `0`, changing `WIDTH` at runtime, and any asynchronous or combinational outputs -- `count` and `overflow` are both registered.

## Deliverable

Copy the complete `modcounter.v` file to `/app/submission/modcounter.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.

## Verification

Five independent, weighted criteria, each a cocotb test running the compiled module cycle-by-cycle against an independent Python reference model, asserting `count` and `overflow` agree every single cycle:

1. **Basic counting.** A fixed modulus, counted through several full wraps. (15%)
2. **Load resets count.** A modulus change mid-count, checked that the stale count is discarded. (25%)
3. **Overflow timing.** The overflow pulse's exact cycle, across several wraps of different moduli. (20%)
4. **Pause and resume.** `en` deasserted for several cycles, then reasserted, checked that state holds exactly and counting resumes correctly. (20%)
5. **A longer randomized mixed sequence** combining load/enable/pause transitions, checked every cycle. (20%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only Icarus Verilog and cocotb are available at verification time; no network access.
