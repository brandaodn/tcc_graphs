"""Regressao: FindPivots nao deve perder vertices com rotulos conhecidos.

Executar na raiz do repositorio:
python3 -m unittest discover -s tests -p 'test_find_pivots.py' -v
"""
import math
import unittest
from collections import defaultdict

from graphs.graphs import Graph
from graphs.batch_pq import TotalOrder
from graphs.duan_et_al import find_pivots


class TestFindPivots(unittest.TestCase):
    def test_reexplores_previously_relaxed_vertices(self):
        g = Graph()
        for v in range(5):
            g.adj[v] = []
        for u, v, w in [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]:
            g.add_edge(u, v, w)

        db = defaultdict(lambda: math.inf)
        db[0] = 0
        order = TotalOrder()
        order.rank(0)

        _, first = find_pivots(g, {0}, order.TOP, db, 2, order)
        self.assertTrue({0, 1, 2}.issubset(first))

        _, second = find_pivots(g, {0}, order.TOP, db, 2, order)
        self.assertTrue(
            {0, 1, 2}.issubset(second),
            f"Vertices previamente relaxados desapareceram de W: {second}",
        )

    def test_honors_upper_bound(self):
        g = Graph()
        g.add_edge(0, 1, 2)
        g.add_edge(1, 2, 3)
        db = defaultdict(lambda: math.inf)
        db[0] = 0
        order = TotalOrder()
        order.rank(0)
        bound = (3, 0, 0)
        _, W = find_pivots(g, {0}, bound, db, 2, order)
        self.assertIn(1, W)
        self.assertNotIn(2, W)


if __name__ == "__main__":
    unittest.main()
