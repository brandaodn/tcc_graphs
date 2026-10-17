"""Regressão específica do ciclo da fronteira no caso aleatório 21.

Este teste NÃO corrige BMSSP. Comprova que a variante experimental detecta
a repetição antes de executar indefinidamente. A chave repetida e a causa
operacional são observadas pelo rastreador trace_first_reinsertion.py.
"""
import random
import unittest
from graphs.graphs import Graph
from graphs.bmssp_frontier_experimental import (
    RepeatedFrontierError, sssp_frontier_experimental,
)


def case_21():
    rng = random.Random(20261017)
    for _ in range(22):
        n = rng.randint(2, 16)
        p = rng.choice([0.08, 0.2, 0.5])
        edges = [
            (u, v, rng.randint(0, 9))
            for u in range(n) for v in range(n)
            if u != v and rng.random() < p
        ]
        source = rng.randrange(n)
    graph = Graph()
    for v in range(n):
        graph.adj[v] = []
    for u, v, w in edges:
        graph.add_edge(u, v, w)
    return graph, source


class TestRepeatedFrontierCase21(unittest.TestCase):
    def test_known_case_triggers_progress_guard(self):
        graph, source = case_21()
        self.assertEqual(len(graph.adj), 16)
        self.assertEqual(sum(map(len, graph.adj.values())), 132)
        with self.assertRaises(RepeatedFrontierError):
            sssp_frontier_experimental(graph, source, max_iterations=1000)


if __name__ == "__main__":
    unittest.main()
