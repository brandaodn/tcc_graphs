"""Regressão específica: vértice exatamente na fronteira B_i_prime.

Executar:
    python -m unittest discover -s tests -p 'test_frontier_boundary.py' -v

O teste deve FALHAR na implementação defeituosa: não usa expectedFailure.
Não altera o algoritmo ou suas condições.
"""
import math
import unittest

from graphs.graphs import Graph, dijkstra
from graphs.duan_et_al import sssp_duan_et_al
from graphs.duan_et_al_iter import sssp_duan_et_al_iter
from graphs.duan_et_al_opt import sssp_duan_et_al_opt


IMPLEMENTATIONS = (
    sssp_duan_et_al,
    sssp_duan_et_al_iter,
    sssp_duan_et_al_opt,
)


def path_graph():
    graph = Graph()
    for vertex in range(5):
        graph.adj[vertex] = []
    for u, v, w in [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]:
        graph.add_edge(u, v, w)
    return graph


class TestFrontierBoundary(unittest.TestCase):
    def test_boundary_vertex_must_be_processed(self):
        """d(2)=5 na fronteira; seu processamento é necessário para alcançar 3 e 4."""
        graph = path_graph()
        expected = dijkstra(graph, 0)
        self.assertEqual([expected[v] for v in range(5)], [0, 2, 5, 9, 14])
        for algorithm in IMPLEMENTATIONS:
            with self.subTest(implementation=algorithm.__name__):
                actual = algorithm(graph, 0)
                # A distância correta de 2 não é suficiente: o vértice precisa
                # também propagar seus caminhos para 3 e 4.
                for vertex in (2, 3, 4):
                    self.assertEqual(
                        actual.get(vertex, math.inf), expected[vertex],
                        f"{algorithm.__name__}: fronteira não propagada até "
                        f"v={vertex}; esperado={expected}; obtido={actual}",
                    )

    def test_longer_path_keeps_multiple_frontier_transitions(self):
        """Várias transições não devem abandonar vértices ainda pendentes."""
        graph = Graph()
        for vertex in range(7):
            graph.adj[vertex] = []
        for vertex, weight in enumerate((2, 3, 4, 5, 6, 7)):
            graph.add_edge(vertex, vertex + 1, weight)
        expected = dijkstra(graph, 0)
        for algorithm in IMPLEMENTATIONS:
            with self.subTest(implementation=algorithm.__name__):
                observed = algorithm(graph, 0)
                self.assertEqual(
                    [observed.get(v, math.inf) for v in range(7)],
                    [expected[v] for v in range(7)],
                    f"{algorithm.__name__}: perdeu vértices pendentes na fronteira",
                )


if __name__ == "__main__":
    unittest.main()
