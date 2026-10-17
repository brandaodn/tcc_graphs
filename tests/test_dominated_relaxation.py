"""Differential test for strictly dominated candidate guard.

Run from repository root:
  python -m unittest discover -s tests -p 'test_dominated_relaxation.py' -v

Validates an optimization hypothesis without changing production modules.
Candidate > previous cannot update distance or tie; equality must still
call relax and must remain eligible for queue reinsertion.
"""
import ast
import inspect
import textwrap
import math
import random
import unittest
from unittest.mock import patch

from graphs.graphs import Graph, dijkstra
from graphs.batch_pq import TotalOrder
from graphs.bmssp_frontier_experimental import sssp_frontier_experimental


def make_graph(n, density, mode, seed):
    rng = random.Random(seed)
    g = Graph()
    for u in range(n):
        g.adj[u] = []
    for u in range(n):
        for v in range(n):
            if u == v or rng.random() >= density:
                continue
            weight = 0 if mode == "zero" else (
                rng.randint(0, 2) if mode == "small" else rng.randint(1, 20))
            g.add_edge(u, v, weight)
    return g, rng.randrange(n)


class DominatedRelaxationTests(unittest.TestCase):
    def test_guard_is_present_in_recursive_propagation(self):
        # Verifica o codigo efetivamente sob teste, nao apenas TotalOrder.relax.
        from graphs.bmssp_frontier_experimental import bmssp_frontier
        tree = ast.parse(textwrap.dedent(inspect.getsource(bmssp_frontier)))
        matched = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "candidate"
            and len(node.test.ops) == 1
            and isinstance(node.test.ops[0], ast.Gt)
            and isinstance(node.test.comparators[0], ast.Name)
            and node.test.comparators[0].id == "previous"
            and any(isinstance(body, ast.Continue) for body in node.body)
        ]
        self.assertTrue(matched, "Expected early continue for dominated candidates")

    def test_strictly_dominated_relax_does_not_change_order(self):
        from collections import defaultdict
        order = TotalOrder()
        db = defaultdict(lambda: math.inf, {0: 10, 1: 3})
        old_key = order.key(1, db)
        accepted, new_key = order.relax(0, 1, 2, db)
        self.assertFalse(accepted)
        self.assertEqual(old_key, new_key)
        self.assertEqual(db[1], 3)

    def test_equal_candidate_still_calls_relax(self):
        from collections import defaultdict
        order = TotalOrder()
        db = defaultdict(lambda: math.inf, {0: 1, 1: 3})
        order.rank(0)
        order.rank(1)
        _, key = order.relax(0, 1, 2, db)
        self.assertEqual(key[0], 3)

    def test_135_seeded_graphs_reference(self):
        for n in (8, 16, 32, 64, 96):
            for density in (0.03, 0.12, 0.4):
                for mode in ("zero", "small", "positive"):
                    for rep in range(3):
                        seed = 20261017 + rep * 993 + n * 17
                        graph, source = make_graph(n, density, mode, seed)
                        with self.subTest(n=n, p=density, mode=mode, rep=rep):
                            actual = sssp_frontier_experimental(
                                graph, source,
                                quota_pending_probe=True,
                                max_iterations=500
                            )
                            expected = dijkstra(graph, source)
                            self.assertEqual(
                                {v: actual.get(v, math.inf) for v in expected},
                                expected
                            )


if __name__ == '__main__':
    unittest.main()
