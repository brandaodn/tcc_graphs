"""Tests for the explicitly named experimental frontier-completion phase.

Run: python -m unittest discover -s tests -p 'test_frontier_completion.py' -v
"""
import unittest
from math import inf

from graphs.graphs import Graph, dijkstra
from graphs.frontier_completion import finish_frontier


class TestFrontierCompletion(unittest.TestCase):
    def test_partially_discovered_path(self):
        g = Graph()
        for v in range(5):
            g.adj[v] = []
        for u, v, w in [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]:
            g.add_edge(u, v, w)
        provisional = {0: 0, 1: 2, 2: 5, 3: 9, 4: inf}
        self.assertEqual(finish_frontier(g, 0, provisional), dijkstra(g, 0))

    def test_zero_weight_cycle_and_unreachable(self):
        g = Graph()
        for v in range(6):
            g.adj[v] = []
        for u, v, w in [(0, 1, 0), (1, 2, 0), (2, 1, 0),
                        (2, 3, 1), (3, 4, 0)]:
            g.add_edge(u, v, w)
        actual = finish_frontier(g, 0, {0: 0, 1: 0, 2: 0})
        self.assertEqual(actual, dijkstra(g, 0))
        self.assertEqual(actual[5], inf)

    def test_negative_weight_is_rejected(self):
        g = Graph()
        g.add_edge(0, 1, -1)
        with self.assertRaises(ValueError):
            finish_frontier(g, 0, {0: 0})


if __name__ == "__main__":
    unittest.main()
