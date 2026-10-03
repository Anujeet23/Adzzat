Fix the incrementally-built DAG at `/app/repo/toposort` so it actually detects cycles of any length and keeps its topological order valid as edges are added over time. The current implementation only rejects a direct two-node cycle (`add_edge(b, a)` right after `add_edge(a, b)`) -- any longer cycle (`a->b->c->a`) or a self-loop slips through uncaught -- and `order()` just returns node-insertion order, which goes stale the moment an edge is added between two nodes that weren't inserted in a compatible order. Read `/app/TASK_CONTRACT.md` before changing anything; `/app/reproduce.py` demonstrates both bugs live.

## Interface

`toposort.DAG()` implements `add_node(node)` (idempotent), `add_edge(u, v) -> bool` (adds the directed edge and returns `True`, or rejects it and returns `False` if it would create a cycle -- including a self-loop -- leaving the graph completely unchanged on rejection), and `order() -> list` (a topological order of every node added so far, consistent with every edge currently in the graph). Any one valid topological order is acceptable; grading checks the *property*, not one specific tie-break.

## Required guarantees

1. `add_edge(u, v)` must reject any edge that would create a cycle of *any* length through existing edges, not just an immediate reverse edge.
2. A self-loop (`add_edge(n, n)`) is always rejected as a one-node cycle.
3. A rejected `add_edge` call leaves the graph completely unchanged -- no partial or phantom edge.
4. `order()` always returns a permutation of exactly the nodes added so far (via `add_node` or implicitly via `add_edge`), with no omissions or duplicates.
5. `order()` is consistent with *every* edge currently in the graph: for every edge `u -> v`, `u` appears strictly before `v` in the returned order, including edges added after nodes were inserted in an incompatible order, and including edges added since the last call to `order()`.

## What's out of scope

Edge weights, removing nodes or edges once added, and any specific tie-break among nodes with no remaining ordering constraint between them -- more than one valid topological order may exist, and any of them is acceptable.

## Deliverable

Copy the complete `toposort` package to `/app/submission/toposort`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria, each a scripted sequence of `add_node`/`add_edge`/`order()` checks against the actual submitted `DAG` object, validating the *properties* above rather than one exact expected list:

1. **Basic correctness.** A simple chain built in topologically-compatible order. (15%)
2. **Longer-cycle detection.** A 3-edge cycle built through intermediate nodes must be rejected on its closing edge. (25%)
3. **Order consistency under reordering.** Nodes inserted in one order, then an edge added that requires the opposite relative order. (25%)
4. **Rejection leaves the graph unchanged**, checked via both a longer cycle and a self-loop. (20%)
5. **A longer mixed sequence** combining all of the above, checked at multiple points. (15%)

A full pass requires all five; per-criterion outcomes are retained separately for diagnosis. Only the Python standard library is available at verification time; no network access.
