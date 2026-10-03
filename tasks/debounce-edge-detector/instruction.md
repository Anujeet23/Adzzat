Fix the button debouncer at `/app/repo/debounce.v`: once it starts timing toward a new candidate value, it never restarts that timer if the raw input changes again before the timer finishes -- so a genuinely bouncing input can lock in a stale, premature decision instead of the debounce window restarting against each new bounce. It also derives `btn_rise`/`btn_fall` directly from the raw, un-debounced input, so every noisy raw toggle produces a spurious edge pulse instead of only genuine debounced transitions. Read `/app/TASK_CONTRACT.md` before changing anything; `/app/reproduce.py` demonstrates both bugs live.

## Interface

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

`btn_clean` is the debounced level. `btn_rise`/`btn_fall` each pulse high for exactly one cycle when `btn_clean` itself transitions.

## Required guarantees

1. `btn_clean` only changes to a new value once `btn_raw` has held that value steadily for `DEBOUNCE_CYCLES` consecutive cycles.
2. If `btn_raw` changes again at any point *before* the debounce window completes, the timer restarts against the new value -- it never locks in a decision based on a value `btn_raw` no longer holds.
3. `btn_rise` pulses high for exactly one cycle, only when `btn_clean` itself transitions from `0` to `1` -- never in response to a raw-input toggle that doesn't produce a genuine `btn_clean` transition.
4. `btn_fall` pulses high for exactly one cycle, only when `btn_clean` itself transitions from `1` to `0`, under the same rule.
5. A raw input that bounces for longer than `DEBOUNCE_CYCLES` without ever settling produces no `btn_clean` transition and no edge pulses at all, for as long as the bouncing continues.

## What's out of scope

Asynchronous reset, any debounce algorithm other than "restart the timer on every change," and `DEBOUNCE_CYCLES` values other than the fixed default of `4`.

## Deliverable

Copy the complete `debounce.v` file to `/app/submission/debounce.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.

## Verification

Five independent, weighted criteria, each a cocotb test running the compiled module cycle-by-cycle against an independent Python reference model, asserting `btn_clean`/`btn_rise`/`btn_fall` agree every single cycle:

1. **Basic debounce.** A clean, non-bouncing transition, checked for correct timing. (15%)
2. **Bounce rejected, timer restarts.** A raw input that bounces partway through a debounce window, checked that the window restarts and the final decision reflects the *last* stable value, not the first candidate. (30%)
3. **Edges follow the debounced signal, not the raw one.** A bouncing raw signal that never produces a genuine `btn_clean` transition must never pulse `btn_rise`/`btn_fall`. (25%)
4. **Repeated genuine transitions.** Several real `btn_clean` transitions over time, each producing exactly one correctly-timed edge pulse. (15%)
5. **A longer randomized mixed sequence** of bounces and genuine transitions, checked every cycle. (15%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only Icarus Verilog and cocotb are available at verification time; no network access.
