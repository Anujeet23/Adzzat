"""Reference implementation. Author-only; not shipped to agents.

The key move versus the naive starter: cycle detection does a real
reachability search (can `v` already reach `u`?) instead of checking
only for a direct reverse edge, and `order()` recomputes a fresh
topological order (Kahn's algorithm) from the current edge set every
time, instead of trusting stale insertion order.
"""
from collections import deque


class DAG:
    def __init__(self):
        self._nodes = []
        self._seen = set()
        self._edges = {}  # node -> list of successors, insertion order

    def add_node(self, node):
        if node not in self._seen:
            self._seen.add(node)
            self._nodes.append(node)
            self._edges[node] = []

    def _reaches(self, start, target):
        stack = [start]
        visited = set()
        while stack:
            cur = stack.pop()
            if cur == target:
                return True
            if cur in visited:
                continue
            visited.add(cur)
            stack.extend(self._edges.get(cur, ()))
        return False

    def add_edge(self, u, v):
        self.add_node(u)
        self.add_node(v)
        if v in self._edges[u]:
            return True  # already present, no-op
        if u == v or self._reaches(v, u):
            return False
        self._edges[u].append(v)
        return True

    def order(self):
        indegree = {n: 0 for n in self._nodes}
        for u in self._nodes:
            for v in self._edges[u]:
                indegree[v] += 1
        queue = deque(n for n in self._nodes if indegree[n] == 0)
        result = []
        remaining = dict(indegree)
        while queue:
            n = queue.popleft()
            result.append(n)
            for v in self._edges[n]:
                remaining[v] -= 1
                if remaining[v] == 0:
                    queue.append(v)
        return result
