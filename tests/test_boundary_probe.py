"""Diagnóstico de fronteira inclusiva — NÃO valida fidelidade a Duan et al.

Executar:
  python3 -m unittest discover -s tests -p 'test_boundary_probe.py' -v

A opcao boundary_probe altera o contrato do conjunto retornado pelo BaseCase.
Ela serve somente para pesquisar por que vertices na fronteira desaparecem.
"""
import math
import random
import unittest

from graphs.graphs import Graph, dijkstra
from graphs.bmssp_frontier_experimental import sssp_frontier_experimental


def make_case(index):
    rng = random.Random(20261017)
    for _ in range(index + 1):
        n = rng.randint(2, 16)
        p = rng.choice((0.08, 0.2, 0.5))
        edges = [(u, v, rng.randint(0, 9))
                 for u in range(n) for v in range(n)
                 if u != v and rng.random() < p]
        source = rng.randrange(n)
    graph = Graph()
    for v in range(n):
        graph.adj[v] = []
    for u, v, w in edges:
        graph.add_edge(u, v, w)
    return graph, source


class TestBoundaryProbe(unittest.TestCase):
    def test_100_seeded_random_graphs(self):
        for index in range(100):
            with self.subTest(case=index):
                g, source = make_case(index)
                expected = dijkstra(g, source)
                observed = sssp_frontier_experimental(
                    g, source, max_iterations=1000, boundary_probe=True
                )
                for v, d in expected.items():
                    self.assertEqual(observed.get(v, math.inf), d,
                                     f"case={index}, vertex={v}")

    def test_zero_weight_cycle(self):
        g = Graph()
        for v in range(5):
            g.adj[v] = []
        for u, v, w in ((0, 1, 0), (1, 2, 0), (2, 1, 0),
                        (2, 3, 1), (3, 4, 0)):
            g.add_edge(u, v, w)
        self.assertEqual(
            sssp_frontier_experimental(g, 0, boundary_probe=True),
            dijkstra(g, 0)
        )


if __name__ == "__main__":
    unittest.main()
