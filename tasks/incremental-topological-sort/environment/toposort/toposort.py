"""An incrementally-built directed acyclic graph.

This implementation's cycle check only looks for a direct reverse edge
(`v` already points straight back to `u`), so any longer cycle built
through intermediate nodes -- or a self-loop, which needs the same
direct-reverse check to fire against itself -- slips through uncaught.
`order()` just returns nodes in the order they were first seen, which
goes stale the moment an edge requires two nodes to appear in the
opposite relative order from how they were inserted. See
/app/TASK_CONTRACT.md.
"""


class DAG:
    def __init__(self):
        self._order_seen = []
        self._edges = {}  # node -> set of successors

    def add_node(self, node):
        if node not in self._edges:
            self._edges[node] = set()
            self._order_seen.append(node)

    def add_edge(self, u, v):
        self.add_node(u)
        self.add_node(v)
        if v in self._edges and u in self._edges[v]:
            return False
        self._edges[u].add(v)
        return True

    def order(self):
        return list(self._order_seen)
