"""Regressão de duas falhas remanescentes da variante pending_probe.

Executar:
 python -m unittest discover -s tests -p 'test_pending_probe_failures.py' -v

Os dois subtestes são intencionalmente falhos até a implementação ser corrigida.
"""
import math
import random
import unittest
from graphs.graphs import Graph, dijkstra
from graphs.bmssp_frontier_experimental import sssp_frontier_experimental


def graph_case(weight_mode):
    rng = random.Random(20262105)
    n, probability = 64, 0.03
    g = Graph()
    for v in range(n):
        g.adj[v] = []
    for u in range(n):
        for v in range(n):
            if u == v or rng.random() >= probability:
                continue
            w = (0 if weight_mode == "zero"
                 else rng.randint(1, 20))
            g.add_edge(u, v, w)
    return g, rng.randrange(n)


class PendingProbeFailureTests(unittest.TestCase):
    def test_sparse_64_boundary_losses(self):
        for mode in ("zero", "positive"):
            with self.subTest(mode=mode):
                g, source = graph_case(mode)
                expected = dijkstra(g, source)
                observed = sssp_frontier_experimental(
                    g, source, pending_probe=True, max_iterations=500)
                differences = {
                    v: (expected[v], observed.get(v, math.inf))
                    for v in expected
                    if expected[v] != observed.get(v, math.inf)
                }
                self.assertEqual(differences, {})


if __name__ == "__main__":
    unittest.main()
