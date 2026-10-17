"""Regression of pending vertices stranded at the recursive work quota.

Run: python -m unittest discover -s tests -p 'test_recursive_quota_frontier.py' -v
The test documents a current defect; it must be revised when the frontier
handoff is fixed. It does not assert BMSSP correctness.
"""
import random
import unittest

from graphs.graphs import Graph
from graphs.bmssp_frontier_experimental import sssp_frontier_experimental


def sparse_case(mode):
    rng = random.Random(20262105)
    graph = Graph()
    for vertex in range(64):
        graph.adj[vertex] = []
    for u in range(64):
        for v in range(64):
            if u == v or rng.random() >= 0.03:
                continue
            weight = 0 if mode == "zero" else rng.randint(1, 20)
            graph.add_edge(u, v, weight)
    return graph, rng.randrange(64)


class RecursiveQuotaFrontierTests(unittest.TestCase):
    def test_pending_frontier_survives_at_quota(self):
        for mode, stranded_vertex in (("zero", 32), ("positive", 18)):
            with self.subTest(mode=mode):
                graph, source = sparse_case(mode)
                diagnostics = []
                sssp_frontier_experimental(
                    graph, source, pending_probe=True,
                    diagnostics=diagnostics, max_iterations=500
                )
                exits = [
                    e for e in diagnostics
                    if e.get("reason") == "recursive_exit"
                    and e["level"] == 1 and e["quota_reached"]
                    and any(vertex == repr(stranded_vertex)
                            for vertex, _ in e["remaining_queue"])
                ]
                self.assertTrue(exits,
                    f"Expected stranded vertex {stranded_vertex} "
                    f"at level-1 quota exit in {mode} case")


if __name__ == "__main__":
    unittest.main()
