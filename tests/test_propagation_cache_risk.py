"""Regression for a sparse graph where naive propagation scan caching loses paths.

A local diagnostic memoization experiment skipping previously scanned
(vertex, key) pairs produced incorrect distances on this graph. This test
checks the unoptimized experimental variant, not a cache implementation.

Run: python -m unittest discover -s tests -p 'test_propagation_cache_risk.py' -v
"""
import math
import random
import unittest

from graphs.graphs import Graph, dijkstra
from graphs.bmssp_frontier_experimental import sssp_frontier_experimental


def counterexample():
    n, density = 96, 0.03
    rng = random.Random(20261017 + n * 17 + int(density * 1000) + 1)
    graph = Graph()
    for v in range(n):
        graph.adj[v] = []
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < density:
                graph.add_edge(u, v, rng.randint(1, 20))
    return graph, rng.randrange(n)


class PropagationCacheRiskTests(unittest.TestCase):
    def test_sparse_96_positive_weights(self):
        graph, source = counterexample()
        self.assertEqual(sum(map(len, graph.adj.values())), 260)
        expected = dijkstra(graph, source)
        result = sssp_frontier_experimental(
            graph, source, quota_pending_probe=True, max_iterations=500
        )
        self.assertEqual(
            {v: result.get(v, math.inf) for v in expected},
            expected
        )


if __name__ == "__main__":
    unittest.main()
