Fix the round-robin arbiter at `/app/repo/rr_arbiter.v`: after granting requester `k`, it rotates priority back onto `k` itself instead of past it, so a requester that keeps its request line held continuously is granted again on every subsequent cycle, starving every other requester indefinitely. Read `/app/TASK_CONTRACT.md` for the exact port list and arbitration rule before changing anything; `/app/reproduce.py` demonstrates the starvation live.

## Interface

```
module rr_arbiter #(parameter N = 4) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [N-1:0] req,
    output reg  [N-1:0] grant
);
```

`N` is fixed at `4` for grading. Each cycle, the arbiter grants exactly one requester among those currently asserting `req`, chosen by scanning starting from an internal rotating priority pointer and wrapping around; if no bit of `req` is set, `grant` is all zero.

## Required guarantees

1. When exactly one `req` bit is set, that requester is granted.
2. When multiple `req` bits are set, exactly one is granted, and it is the one nearest to (at or after) the current priority pointer, wrapping around to index `0` if nothing qualifies before the end.
3. After granting requester `k`, the priority pointer moves to `(k + 1) mod N` -- so `k` becomes the *lowest* priority for the next cycle, not the highest.
4. If every requester holds its request line high continuously, grants rotate through all `N` requesters in order, each getting exactly one grant per full rotation of `N` cycles -- no requester is ever skipped or granted twice before the others have had a turn.
5. When no `req` bit is set, `grant` is entirely zero and the priority pointer does not advance.

## What's out of scope

Any `N` other than the fixed default of `4`, request priority weighting, and any combinational (same-cycle) path from `req` to `grant` -- `grant` is registered.

## Deliverable

Copy the complete `rr_arbiter.v` file to `/app/submission/rr_arbiter.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.

## Verification

Five independent, weighted criteria, each a cocotb test running the compiled module cycle-by-cycle against an independent Python reference model, asserting `grant` agrees every single cycle:

1. **Single requester.** Exactly one `req` bit active at a time. (15%)
2. **Fairness under continuous contention.** All requesters held high; grants must rotate through everyone, not repeat. (30%)
3. **Partial contention.** A subset of requesters held high, checked for fair alternation among just that subset. (20%)
4. **Dynamic request changes.** Requesters join and leave over time, grant always tracks correctly. (15%)
5. **A longer randomized mixed sequence** of request patterns, checked every cycle. (20%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only Icarus Verilog and cocotb are available at verification time; no network access.
