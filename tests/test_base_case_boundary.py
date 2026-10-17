"""Contratos do limite exclusivo de BaseCase (k+1 vertices extraidos).

Executar na raiz do repositorio:
    python -m unittest discover -s tests -p 'test_base_case_boundary.py' -v

A chamada BaseCase retorna (B', U) em que os vertices com chave < B'
podem ser declarados processados nesta chamada. O vertice com chave igual
a B' e mantido fora de U. Os testes nao substituem verificacao formal.
"""
import math
import unittest
from collections import defaultdict

from graphs.graphs import Graph
from graphs.batch_pq import TotalOrder
from graphs.duan_et_al import base_case


def path():
    g = Graph()
    for v in range(5):
        g.adj[v] = []
    for u, v, w in [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]:
        g.add_edge(u, v, w)
    return g


class TestBaseCaseBoundary(unittest.TestCase):
    def test_k_plus_one_uses_exclusive_boundary(self):
        g = path()
        db = defaultdict(lambda: math.inf)
        db[0] = 0
        order = TotalOrder()
        order.rank(0)
        boundary, complete = base_case(g, 0, order.TOP, db, 2, order)
        self.assertEqual(boundary, order.key(2, db))
        self.assertEqual(complete, {0, 1})
        self.assertNotIn(2, complete)
        self.assertLess(order.key(1, db), boundary)

    def test_already_discovered_boundary_vertex_stays_pending(self):
        g = path()
        db = defaultdict(lambda: math.inf)
        db.update({0: 0, 1: 2, 2: 5})
        order = TotalOrder()
        order.rank(0)
        order.rank(1)
        order.rank(2)
        # Reconstitui a ordem dos saltos antes da segunda descoberta.
        order.hops[0], order.hops[1], order.hops[2] = 0, 1, 2
        order.pred[1], order.pred[2] = 0, 1
        boundary, complete = base_case(g, 0, order.TOP, db, 2, order)
        self.assertEqual(boundary, order.key(2, db))
        self.assertEqual(complete, {0, 1})

    def test_under_capacity_returns_upper_bound(self):
        g = Graph()
        g.adj[0] = [(1, 2)]
        g.adj[1] = []
        db = defaultdict(lambda: math.inf)
        db[0] = 0
        order = TotalOrder()
        order.rank(0)
        bound, complete = base_case(g, 0, order.TOP, db, 2, order)
        self.assertEqual(bound, order.TOP)
        self.assertEqual(complete, {0, 1})

    def test_zero_weight_path_has_distinct_total_order_keys(self):
        g = Graph()
        for v in range(4):
            g.adj[v] = []
        for u in range(3):
            g.add_edge(u, u + 1, 0)
        db = defaultdict(lambda: math.inf)
        db[0] = 0
        order = TotalOrder()
        order.rank(0)
        bound, complete = base_case(g, 0, order.TOP, db, 2, order)
        self.assertEqual(complete, {0, 1})
        self.assertEqual(bound, order.key(2, db))


if __name__ == '__main__':
    unittest.main()
