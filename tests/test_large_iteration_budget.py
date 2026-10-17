"""Regression: a 1,024-vertex graph needs more than 1,000 distinct
BMSSP level-1 iterations; reaching the diagnostic budget is not itself
proof of a repeated frontier.

Run: python -m unittest discover -s tests -p 'test_large_iteration_budget.py' -v
"""
import math
import random
import unittest

from graphs.graphs import Graph, dijkstra
from graphs.bmssp_frontier_experimental import (
    RepeatedFrontierError, sssp_frontier_experimental,
)


class TestLargeIterationBudget(unittest.TestCase):
    def test_1024_graph_finishes_with_larger_diagnostic_budget(self):
        n = 1024
        probability = 0.12
        seed = 20261017 + n * 17 + int(probability * 1000)
        rng = random.Random(seed)
        graph = Graph()
        for vertex in range(n):
            graph.adj[vertex] = []
        for u in range(n):
            for v in range(n):
                if u != v and rng.random() < probability:
                    graph.add_edge(u, v, rng.randint(0, 20))
        source = rng.randrange(n)
        self.assertEqual(source, 810)
        self.assertEqual(sum(len(e) for e in graph.adj.values()), 125402)
        actual = sssp_frontier_experimental(
            graph, source, quota_pending_probe=True, max_iterations=10000
        )
        expected = dijkstra(graph, source)
        self.assertEqual(
            {v: actual.get(v, math.inf) for v in expected}, expected
        )


if __name__ == "__main__":
    unittest.main()
