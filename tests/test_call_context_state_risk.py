"""Diagnóstico de repeticoes com o mesmo contexto e estado de fila diferente.

Nao assume que cache por contexto seja correto. Uma nova varredura pode
precisar inserir candidatos numa fila que mudou desde a primeira passagem.
Este teste conserva o contraexemplo deterministico da topologia gerada.
"""
import random
import unittest
from graphs.graphs import Graph, dijkstra
from graphs.bmssp_frontier_experimental import sssp_frontier_experimental


def make_dense_case():
    n, probability = 96, .4
    rng = random.Random(20261017 + n * 17 + int(probability * 1000) + 1)
    graph = Graph()
    for v in range(n):
        graph.adj[v] = []
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < probability:
                graph.add_edge(u, v, rng.randint(1, 20))
    return graph, rng.randrange(n)


class CallContextStateTests(unittest.TestCase):
    def test_96_node_dense_positive_reference(self):
        graph, source = make_dense_case()
        observed = sssp_frontier_experimental(
            graph, source, quota_pending_probe=True, max_iterations=500
        )
        self.assertEqual(observed, dijkstra(graph, source))


if __name__ == '__main__':
    unittest.main()
