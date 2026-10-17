"""Testes diferenciais de SSSP: Dijkstra/Bellman-Ford versus BMSSP.

Executar na raiz do repositório:
    python -m unittest discover -s tests -p 'test_*.py' -v

Não modifica os algoritmos. Uma falha mostra arestas e distâncias para reprodução.
"""
import math
import random
import unittest

from graphs.graphs import Graph, bellman_ford, dijkstra
from graphs.degree_reduction import bounded_out_degree
from graphs.duan_et_al import sssp_duan_et_al
from graphs.duan_et_al_iter import sssp_duan_et_al_iter
from graphs.duan_et_al_opt import sssp_duan_et_al_opt


BMSSP = (
    sssp_duan_et_al,
    sssp_duan_et_al_iter,
    sssp_duan_et_al_opt,
)


def make_graph(vertices, edges):
    """Preserva inclusive vértices isolados e vértices apenas de destino."""
    graph = Graph()
    for vertex in vertices:
        graph.adj[vertex] = []
    for u, v, weight in edges:
        if weight < 0:
            raise ValueError("Os testes de SSSP exigem pesos não negativos")
        graph.add_edge(u, v, weight)
    return graph


def all_vertices(graph):
    return set(graph.adj) | {
        v for edges in graph.adj.values() for v, _ in edges
    }


def mismatch(reference, actual, vertices):
    """Compara distâncias finitas e infinitas sem subtrair infinito."""
    errors = []
    for vertex in vertices:
        expected = reference.get(vertex, math.inf)
        observed = actual.get(vertex, math.inf)
        if math.isnan(expected) or math.isnan(observed):
            ok = False
        elif math.isinf(expected) or math.isinf(observed):
            ok = expected == observed
        else:
            ok = math.isclose(expected, observed, rel_tol=0, abs_tol=1e-9)
        if not ok:
            errors.append((vertex, expected, observed))
    return errors


class TestSSSPDifferential(unittest.TestCase):
    def check_graph(self, vertices, edges, source, transformed=False):
        graph = make_graph(vertices, edges)
        if transformed:
            graph = bounded_out_degree(graph, max_degree=2)

        expected_vertices = all_vertices(graph) | {source}
        reference = bellman_ford(graph, source)
        dijkstra_result = dijkstra(graph, source)

        self.assertFalse(
            mismatch(reference, dijkstra_result, expected_vertices),
            "Dijkstra diverge de Bellman-Ford: "
            f"source={source}, edges={edges}",
        )

        for algorithm in BMSSP:
            with self.subTest(
                algorithm=algorithm.__name__,
                source=source,
                transformed=transformed,
                edges=edges,
            ):
                actual = algorithm(graph, source)
                errors = mismatch(reference, actual, expected_vertices)
                self.assertFalse(
                    errors,
                    f"{algorithm.__name__} incorreto; "
                    f"source={source}; transformed={transformed}; "
                    f"vertices={vertices}; edges={edges}; "
                    f"divergences={errors}; expected={dict(reference)}; "
                    f"actual={actual}",
                )

    def test_single_vertex(self):
        self.check_graph([0], [], 0)

    def test_simple_path(self):
        self.check_graph(
            list(range(5)),
            [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)],
            0,
        )

    def test_disconnected(self):
        self.check_graph(
            list(range(6)),
            [(0, 1, 2), (1, 2, 3), (3, 4, 1)],
            0,
        )

    def test_zero_weight_cycle(self):
        self.check_graph(
            list(range(5)),
            [(0, 1, 0), (1, 2, 0), (2, 1, 0),
             (2, 3, 1), (0, 3, 5), (3, 4, 0)],
            0,
        )

    def test_equal_shortest_paths(self):
        self.check_graph(
            list(range(5)),
            [(0, 1, 1), (0, 2, 1), (1, 3, 1),
             (2, 3, 1), (1, 4, 2), (3, 4, 1)],
            0,
        )

    def test_high_degree(self):
        vertices = list(range(9))
        edges = [(0, v, v % 3) for v in range(1, 9)]
        edges += [(v, 8, 2) for v in range(1, 8)]
        self.check_graph(vertices, edges, 0)
        self.check_graph(vertices, edges, 0, transformed=True)

    def test_random_small_graphs(self):
        """Reproduzível: semente e índice do caso aparecem na saída."""
        rng = random.Random(20261017)
        for case in range(30):
            n = rng.randint(2, 16)
            vertices = list(range(n))
            probability = rng.choice([0.08, 0.2, 0.5])
            edges = [
                (u, v, rng.randint(0, 9))
                for u in vertices for v in vertices
                if u != v and rng.random() < probability
            ]
            source = rng.randrange(n)
            with self.subTest(case=case, n=n, probability=probability):
                self.check_graph(vertices, edges, source)

    def test_degree_reduction_preserves_distances(self):
        """Confere distâncias entre vértices originais após transformação."""
        vertices = list(range(12))
        edges = [(0, v, v % 4) for v in range(1, 12)]
        edges += [(v, (v + 1) % 12, 1) for v in range(1, 12)]
        original = make_graph(vertices, edges)
        transformed = bounded_out_degree(original)
        self.assertTrue(all(len(es) <= 2 for es in transformed.adj.values()))
        before = bellman_ford(original, 0)
        after = bellman_ford(transformed, 0)
        self.assertFalse(mismatch(before, after, vertices))


if __name__ == "__main__":
    unittest.main()
