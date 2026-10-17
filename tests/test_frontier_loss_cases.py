"""Regressoes diferenciais dos quatro casos onde a filtragem de reinsercao
elimina ciclos mas pode descartar vertices necessarios.

Executar: python -m unittest discover -s tests -p 'test_frontier_loss_cases.py' -v
Estes testes sao criterios de aceitacao e DEVEM falhar enquanto a variante
experimental nao tiver corrigido a perda da fronteira.
"""
import math
import random
import unittest

from graphs.graphs import Graph, dijkstra
from graphs.bmssp_frontier_experimental import (
    sssp_frontier_experimental, RepeatedFrontierError,
)


def reproduce_case(case):
    rng = random.Random(20261017)
    for _ in range(case + 1):
        n = rng.randint(2, 16)
        probability = rng.choice([0.08, 0.2, 0.5])
        edges = [(u, v, rng.randint(0, 9))
                 for u in range(n) for v in range(n)
                 if u != v and rng.random() < probability]
        source = rng.randrange(n)
    g = Graph()
    for u in range(n):
        g.adj[u] = []
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g, source


class TestFrontierLossCases(unittest.TestCase):
    def test_four_known_shortest_path_failures(self):
        for case in (8, 11, 13, 23):
            with self.subTest(case=case):
                graph, source = reproduce_case(case)
                expected = dijkstra(graph, source)
                try:
                    actual = sssp_frontier_experimental(
                        graph, source, max_iterations=1000)
                except RepeatedFrontierError as exc:
                    self.fail(f"case={case}: fronteira repetida: {exc}")
                errors = {
                    vertex: (expected[vertex], actual.get(vertex, math.inf))
                    for vertex in expected
                    if actual.get(vertex, math.inf) != expected[vertex]
                }
                self.assertFalse(errors, f"case={case}: {errors}")


if __name__ == "__main__":
    unittest.main()
