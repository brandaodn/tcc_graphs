"""Diagnostica progresso real do BMSSP, sem alterar implementações de produção.

python -m unittest discover -s tests -p 'test_frontier_progress.py' -v
"""
import math
import unittest
from graphs.batch_pq import BatchPQ
from graphs.graphs import Graph, dijkstra
from graphs.bmssp_frontier_experimental import (
    sssp_frontier_experimental, RepeatedFrontierError,
)


class TestFrontierProgress(unittest.TestCase):
    def test_pull_must_not_ignore_live_vertex_behind_stale_prefix(self):
        q = BatchPQ(M=1, B=(math.inf,) * 3)
        q.insert(1, (20, 0, 1))
        q.insert(1, (10, 0, 1))
        q.insert(2, (30, 0, 2))
        first_boundary, first = q.pull()
        self.assertEqual(first, [1])
        second_boundary, second = q.pull()
        self.assertEqual(second, [2])
        self.assertTrue(q.is_empty())

    def test_pull_should_return_actual_live_boundary(self):
        q = BatchPQ(M=1, B=(math.inf,) * 3)
        q.batch_prepend([(1, (21, 0, 1))])
        q.batch_prepend([(2, (24, 0, 2))])
        boundary, vertices = q.pull()
        # A fila genérica deve extrair o menor globalmente;
        # se BatchPrepend exigir pré-condição mais forte, este
        # teste deve ser separado do contrato formal do artigo.
        self.assertEqual(vertices, [1])
        self.assertEqual(boundary, (24, 0, 2))

    def test_repeated_frontier_is_reported_not_silently_accepted(self):
        g = Graph()
        for v in range(5):
            g.adj[v] = []
        for u, v, w in ((0, 1, 2), (1, 2, 3),
                        (2, 3, 4), (3, 4, 5)):
            g.add_edge(u, v, w)
        expected = dijkstra(g, 0)
        actual = sssp_frontier_experimental(g, 0, max_iterations=200)
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
