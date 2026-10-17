"""Auditoria de invariante formal: retorno BMSSP deve excluir a fronteira.

Com boundary_probe=True espera-se uma FALHA: a variante foi criada como
experimento de propagacao, nao como implementacao comprovada de Duan et al.
Executar: python -m unittest discover -s tests -p 'test_boundary_contract.py' -v
"""
import math
import unittest
from collections import defaultdict

from graphs.graphs import Graph
from graphs.batch_pq import TotalOrder
from graphs.bmssp_frontier_experimental import bmssp_frontier


def scenario():
    graph = Graph()
    for v in range(5):
        graph.adj[v] = []
    for u, v, w in [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]:
        graph.add_edge(u, v, w)
    return graph


class TestBoundaryContract(unittest.TestCase):
    def run_base(self, probe):
        graph = scenario()
        dist = defaultdict(lambda: math.inf)
        dist[0] = 0
        order = TotalOrder()
        order.rank(0)
        return bmssp_frontier(
            graph, 0, order.TOP, {0}, dist, 2, 2, order,
            diagnostics=[], boundary_probe=probe
        ), dist, order

    def test_exclusive_boundary_reference(self):
        (boundary, complete), dist, order = self.run_base(False)
        self.assertEqual(boundary, order.key(2, dist))
        self.assertEqual(complete, {0, 1})
        self.assertTrue(all(order.key(v, dist) < boundary for v in complete))

    def test_experimental_probe_preserves_exclusive_return_contract(self):
        (boundary, complete), dist, order = self.run_base(True)
        self.assertTrue(
            all(order.key(v, dist) < boundary for v in complete),
            f"boundary_probe violated exclusive BMSSP contract: "
            f"boundary={boundary}, Ui={complete}, "
            f"equal_boundary={[v for v in complete if order.key(v, dist) == boundary]}"
        )


if __name__ == "__main__":
    unittest.main()
