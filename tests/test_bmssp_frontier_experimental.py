"""Regressões da etapa 2 para variante BMSSP de fronteira.

O teste exige resultados corretos ou falha explícita com
RepeatedFrontierError; não permite completar por Dijkstra.
"""
import unittest
from math import inf
from graphs.graphs import Graph, dijkstra
from graphs.bmssp_frontier_experimental import (
    sssp_frontier_experimental, RepeatedFrontierError,
)


def graph_with_edges(n, edges):
    g = Graph()
    for v in range(n):
        g.adj[v] = []
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g


class TestBMSSPFrontierExperimental(unittest.TestCase):
    def check_graph(self, graph, source=0):
        try:
            observed = sssp_frontier_experimental(
                graph, source, max_iterations=1000)
        except RepeatedFrontierError as exc:
            self.fail(f"Fronteira recursiva nao progrediu: {exc}")
        expected = dijkstra(graph, source)
        self.assertEqual(
            [observed.get(v, inf) for v in expected],
            [expected[v] for v in expected],
        )

    def test_five_vertex_path(self):
        g = graph_with_edges(5, [
            (0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)])
        self.check_graph(g)

    def test_seven_vertex_path(self):
        g = graph_with_edges(
            7, [(u, u + 1, w)
                for u, w in enumerate((2, 3, 4, 5, 6, 7))])
        self.check_graph(g)

    def test_zero_weight_cycle(self):
        g = graph_with_edges(5, [
            (0, 1, 0), (1, 2, 0), (2, 1, 0),
            (2, 3, 1), (3, 4, 0)])
        self.check_graph(g)


if __name__ == "__main__":
    unittest.main()
