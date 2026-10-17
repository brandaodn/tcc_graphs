"""Differential regression for the experimental recursive queue-residue handoff.

Run:
 python -m unittest discover -s tests -p 'test_quota_pending_probe.py' -v

Passing these tests does not prove the BMSSP time bound or article equivalence.
"""
import math
import random
import unittest

from graphs.graphs import Graph, dijkstra
from graphs.bmssp_frontier_experimental import sssp_frontier_experimental


def graph_case(n, density, mode, seed):
    rng = random.Random(seed)
    graph = Graph()
    for v in range(n):
        graph.adj[v] = []
    for u in range(n):
        for v in range(n):
            if u == v or rng.random() >= density:
                continue
            weight = (0 if mode == "zero" else
                      rng.randint(0, 2) if mode == "small" else
                      rng.randint(1, 20))
            graph.add_edge(u, v, weight)
    return graph, rng.randrange(n)


class QuotaPendingProbeTests(unittest.TestCase):
    def assert_matches_reference(self, graph, source):
        observed = sssp_frontier_experimental(
            graph, source,
            quota_pending_probe=True, max_iterations=500
        )
        expected = dijkstra(graph, source)
        self.assertEqual(
            {v: observed.get(v, math.inf) for v in expected},
            expected
        )

    def test_known_sparse_counterexamples(self):
        for mode in ("zero", "positive"):
            with self.subTest(mode=mode):
                g, source = graph_case(64, .03, mode, 20262105)
                self.assert_matches_reference(g, source)

    def test_108_size_density_weight_cases(self):
        for n in (8, 16, 32, 64):
            for density in (.03, .12, .4):
                for mode in ("zero", "small", "positive"):
                    for repetition in range(3):
                        seed = 20261017 + repetition * 993 + n * 17
                        with self.subTest(n=n, density=density, mode=mode,
                                          seed=seed):
                            graph, source = graph_case(
                                n, density, mode, seed)
                            self.assert_matches_reference(graph, source)


if __name__ == "__main__":
    unittest.main()
