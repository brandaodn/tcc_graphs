"""Extended diagnostic differential coverage for boundary_probe=True.

Run from repository root:
  python -m unittest discover -s tests -p 'test_boundary_stress.py' -v

Diagnostic only. Passing distances does not prove compliance with Duan et al.,
nor does it validate the claimed asymptotic complexity.
"""
import math
import random
import unittest

from graphs.graphs import Graph, dijkstra
from graphs.bmssp_frontier_experimental import sssp_frontier_experimental


class TestBoundaryStress(unittest.TestCase):
    def test_graph_sizes_densities_and_weight_distributions(self):
        case_number = 0
        for n in (8, 16, 32, 64):
            for probability in (0.03, 0.12, 0.4):
                for weights in ("zero", "small", "positive"):
                    for repetition in range(3):
                        seed = 20261017 + repetition * 993 + n * 17
                        rng = random.Random(seed)
                        graph = Graph()
                        for vertex in range(n):
                            graph.adj[vertex] = []
                        for u in range(n):
                            for v in range(n):
                                if u == v or rng.random() >= probability:
                                    continue
                                weight = (
                                    0 if weights == "zero"
                                    else rng.randint(0, 2) if weights == "small"
                                    else rng.randint(1, 20)
                                )
                                graph.add_edge(u, v, weight)
                        source = rng.randrange(n)
                        with self.subTest(
                            case=case_number, n=n, p=probability,
                            weights=weights, seed=seed, source=source
                        ):
                            reference = dijkstra(graph, source)
                            actual = sssp_frontier_experimental(
                                graph, source,
                                boundary_probe=True,
                                max_iterations=500
                            )
                            errors = {
                                v: (reference[v], actual.get(v, math.inf))
                                for v in reference
                                if actual.get(v, math.inf) != reference[v]
                            }
                            self.assertFalse(errors, f"case={case_number}: {errors}")
                        case_number += 1


if __name__ == "__main__":
    unittest.main()
