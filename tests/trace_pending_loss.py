"""Trace shortest-path edges missing from pending_probe recursion.

Run from repo root:
  python -m tests.trace_pending_loss

Reconstructs sparse 64-vertex failures with fixed seeds. It reports the
shortest path and the first vertex whose tentative BMSSP distance diverges.
This is diagnostic only; no production algorithm is changed.
"""
import math
import random
from collections import defaultdict
from graphs.graphs import Graph, dijkstra
from graphs.bmssp_frontier_experimental import sssp_frontier_experimental


def make_graph(mode):
    rng = random.Random(20262105)
    n = 64
    graph = Graph()
    for u in range(n):
        graph.adj[u] = []
    for u in range(n):
        for v in range(n):
            if u == v or rng.random() >= 0.03:
                continue
            weight = 0 if mode == "zero" else rng.randint(1, 20)
            graph.add_edge(u, v, weight)
    return graph, rng.randrange(n)


def reference_with_parents(graph, source):
    import heapq
    dist = {v: math.inf for v in graph.adj}
    parent = {}
    dist[source] = 0
    heap = [(0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d != dist[u]:
            continue
        for v, w in graph.adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                parent[v] = u
                heapq.heappush(heap, (dist[v], v))
    return dist, parent


def path_to(v, parent):
    result = [v]
    while result[-1] in parent:
        result.append(parent[result[-1]])
    return result[::-1]


def main():
    for mode, targets in (("zero", (17, 40)), ("positive", (28,))):
        graph, source = make_graph(mode)
        expected, parent = reference_with_parents(graph, source)
        obtained = sssp_frontier_experimental(
            graph, source, pending_probe=True, max_iterations=500
        )
        print(f"mode={mode} source={source}")
        for target in targets:
            path = path_to(target, parent)
            labels = [(v, expected[v], obtained.get(v, math.inf)) for v in path]
            print(f"target={target} path={path} labels={labels}")
            first = next((v for v in path
                          if expected[v] != obtained.get(v, math.inf)), None)
            print(f"first_missing={first}")


if __name__ == "__main__":
    main()
