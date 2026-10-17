"""Etapa 1: invariantes de BaseCase, FindPivots e filas.

Executar: python -m unittest discover -s tests -p 'test_stage1_invariants.py' -v
Testes de contrato; nao substituem a validacao diferencial de SSSP.
"""
import math
import unittest
from collections import defaultdict
from unittest.mock import patch

from graphs.graphs import Graph
from graphs.batch_pq import TotalOrder, BatchPQ, BatchPQFast
from graphs.duan_et_al import base_case, find_pivots


def make_graph(edges, n):
    g = Graph()
    for v in range(n):
        g.adj[v] = []
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g


class TestStage1Invariants(unittest.TestCase):
    def test_base_case_skips_stale_heap_record(self):
        # 0 -> 1 (10), 0 -> 2 (1), 2 -> 1 (1)
        # O registro antigo de 1 (10) deve ser ignorado quando d(1)=2.
        g = make_graph([(0, 1, 10), (0, 2, 1), (2, 1, 1),
                        (1, 3, 1)], 4)
        db = defaultdict(lambda: math.inf)
        db[0] = 0
        order = TotalOrder()
        order.rank(0)
        bound, explored = base_case(g, 0, order.TOP, db, 3, order)
        self.assertEqual(db[1], 2)
        self.assertTrue({0, 2, 1}.issubset(explored))
        self.assertEqual(db[3], 3)

    def test_find_pivots_reexplores_labels_without_key_improvement(self):
        g = make_graph([(0, 1, 0), (1, 2, 0), (2, 1, 0), (2, 3, 1)], 4)
        db = defaultdict(lambda: math.inf)
        db[0] = 0
        order = TotalOrder()
        order.rank(0)
        _, first = find_pivots(g, {0}, order.TOP, db, 3, order)
        _, second = find_pivots(g, {0}, order.TOP, db, 3, order)
        self.assertEqual(first, second)
        self.assertTrue({0, 1, 2}.issubset(second))

    def test_find_pivots_bound_prevents_out_of_range(self):
        g = make_graph([(0, 1, 1), (1, 2, 4)], 3)
        db = defaultdict(lambda: math.inf)
        db[0] = 0
        order = TotalOrder()
        order.rank(0)
        _, visited = find_pivots(g, {0}, (2, 0, 0), db, 3, order)
        self.assertIn(1, visited)
        self.assertNotIn(2, visited)

    def test_batch_pq_live_entry_consistency(self):
        top = (math.inf,) * 3
        for typ in (BatchPQ, BatchPQFast):
            with self.subTest(typ=typ.__name__):
                q = typ(M=2, B=top)
                q.insert(1, (9, 0, 1))
                q.insert(1, (2, 0, 1))
                q.insert(2, (3, 0, 2))
                self.assertEqual(q._key_val, {1: (2, 0, 1), 2: (3, 0, 2)})
                returned = []
                for _ in range(3):
                    _, vertices = q.pull()
                    returned.extend(vertices)
                    if q.is_empty():
                        break
                self.assertEqual(set(returned), {1, 2})
                self.assertEqual(len(returned), 2)
                self.assertTrue(q.is_empty())


if __name__ == "__main__":
    unittest.main()
