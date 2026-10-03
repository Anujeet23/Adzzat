# Incremental topological sort — contract

Source: an original, minimal starter at `/app/repo/toposort`, not a fork of an existing project.

## API

```python
class DAG:
    def add_node(self, node) -> None: ...   # idempotent
    def add_edge(self, u, v) -> bool: ...     # False (unchanged) if it would create a cycle
    def order(self) -> list: ...               # a valid topological order of all nodes so far
```

## Guarantees

1. **Full cycle detection.** `add_edge(u, v)` rejects (`False`) any edge that would create a cycle of any length through the graph's existing edges, not merely a direct reverse edge.
2. **Self-loops rejected.** `add_edge(n, n)` always returns `False`.
3. **Atomic rejection.** A rejected `add_edge` call leaves the graph exactly as it was -- no partial or phantom edge is ever added.
4. **Complete order.** `order()` returns a permutation of exactly the nodes added so far (via `add_node` or implicitly via `add_edge`), no omissions, no duplicates.
5. **Order validity.** For every edge `u -> v` currently in the graph, `u` appears strictly before `v` in the result of `order()` -- including edges added after nodes were inserted in an incompatible order, and including edges added since the previous call to `order()`. Any one valid topological order is acceptable; there is no required tie-break among nodes with no ordering constraint between them.

## What's out of scope

Edge weights, removing nodes or edges once added, and any specific tie-break when multiple valid orders exist.

## Delivery

Copy the complete `toposort` package to `/app/submission/toposort`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
