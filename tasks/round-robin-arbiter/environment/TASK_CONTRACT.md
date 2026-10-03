# Round-robin arbiter — contract

Source: an original, minimal starter at `/app/repo/rr_arbiter.v`, not a fork of an existing project.

## Port list

```
module rr_arbiter #(parameter N = 4) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [N-1:0] req,
    output reg  [N-1:0] grant
);
```

`N=4`, fixed for grading. `rst_n` active-low, synchronous.

## Guarantees

1. **Single requester served.** Exactly one `req` bit set -> that requester granted.
2. **Nearest-to-pointer selection.** Multiple `req` bits set -> the one nearest to (at or after) the priority pointer, wrapping, is granted.
3. **Pointer rotates past the winner.** After granting `k`, the pointer becomes `(k + 1) mod N`.
4. **Round-robin fairness.** All requesters held high continuously -> grants visit every requester once per `N`-cycle rotation, in order, none skipped or repeated early.
5. **No request, no grant, no rotation.** `req == 0` -> `grant == 0` and the pointer does not move.

## What's out of scope

Any `N` other than `4`; priority weighting; any combinational req-to-grant path (`grant` is registered).

## Delivery

Copy the complete `rr_arbiter.v` file to `/app/submission/rr_arbiter.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.
