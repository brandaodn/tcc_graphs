"""Experimento de diagnóstico de BaseCase e propagação em BMSSP.

Executar: python3 -m unittest discover -s tests -p 'test_base_case_diagnostic.py' -v
Os testes descrevem o comportamento matematicamente esperado: podem falhar
até que o algoritmo seja corrigido. Não alteram os módulos de produção.
"""
import math
import unittest
from collections import defaultdict

from graphs.graphs import Graph, dijkstra
from graphs.batch_pq import TotalOrder
from graphs.duan_et_al import base_case, find_pivots
from graphs.duan_et_al import sssp_duan_et_al
from graphs.duan_et_al_iter import sssp_duan_et_al_iter
from graphs.duan_et_al_opt import sssp_duan_et_al_opt


def path_graph():
    graph = Graph()
    for u in range(5):
        graph.adj[u] = []
    for u, v, w in ((0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)):
        graph.add_edge(u, v, w)
    return graph


class TestBaseCaseDiagnostic(unittest.TestCase):
    def test_base_case_explores_previously_discovered_vertices(self):
        graph = path_graph()
        db = defaultdict(lambda: math.inf)
        db[0] = 0
        order = TotalOrder()
        order.rank(0)
        pivots, seen = find_pivots(graph, {0}, order.TOP, db, 2, order)
        self.assertEqual(pivots, {0})
        self.assertEqual(seen, {0, 1, 2})
        bound, result = base_case(graph, 0, order.TOP, db, 2, order)
        self.assertIn(
            1, result,
            f"BaseCase perdeu um vértice descoberto (U={result}, B={bound})",
        )

    def test_path_distances_reach_last_vertex(self):
        graph = path_graph()
        expected = dijkstra(graph, 0)
        self.assertEqual(expected[4], 14)
        for algorithm in (sssp_duan_et_al,
                          sssp_duan_et_al_iter,
                          sssp_duan_et_al_opt):
            with self.subTest(algorithm=algorithm.__name__):
                observed = algorithm(graph, 0)
                self.assertEqual(
                    observed.get(4, math.inf), 14,
                    f"vértice 4 ausente, distâncias observadas: {observed}",
                )


if __name__ == "__main__":
    unittest.main()
