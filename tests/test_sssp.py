"""Testes de corretude: cada implementação do BMSSP deve produzir as mesmas
distâncias que o Dijkstra.

Executar a partir da raiz do repositório:
    python -m unittest discover tests
"""
import random
import unittest

from graphs.degree_reduction import AuxVertex
from graphs import (
    Graph,
    dijkstra,
    count_dist_errors,
    shortest_path,
    bounded_out_degree,
    constant_degree,
    sssp_duan_et_al,
    sssp_duan_et_al_iter,
    sssp_duan_et_al_opt,
    sssp_duan_et_al_fast,
)

ALGORITHMS = (sssp_duan_et_al, sssp_duan_et_al_iter, sssp_duan_et_al_opt,
              sssp_duan_et_al_fast)


def random_graph(rng, n, m):
    g = Graph()
    for v in range(n):
        g.adj[v]
    for _ in range(m):
        u, v = rng.randrange(n), rng.randrange(n)
        if u != v:
            # Mistura pesos pequenos (muitos empates) e grandes
            w = rng.choice([rng.randint(1, 3), rng.randint(1, 1000)])
            g.add_edge(u, v, w)
    return g


class TestSSSP(unittest.TestCase):

    def check(self, g, source=0):
        ref = dijkstra(g, source)
        for alg in ALGORITHMS:
            with self.subTest(algorithm=alg.__name__):
                self.assertEqual(count_dist_errors(ref, alg(g, source)), 0)

    def test_random_graphs(self):
        # Com a semente 1, a BatchPQ antiga (coleta contando entradas
        # obsoletas) falhava em 3 destes 3000 grafos.
        rng = random.Random(1)
        for _ in range(3000):
            n = rng.randint(5, 300)
            self.check(random_graph(rng, n, rng.randint(n, 4 * n)))

    def test_random_graphs_bounded_degree(self):
        rng = random.Random(2)
        for _ in range(300):
            n = rng.randint(5, 300)
            self.check(bounded_out_degree(random_graph(rng, n, rng.randint(n, 4 * n)), 2))

    def test_random_graphs_constant_degree(self):
        # Ciclos de peso zero: antes de o relaxamento rejeitar empates piores
        # na ordem total, o BMSSP entrava em laço infinito nestes grafos
        rng = random.Random(5)
        for _ in range(300):
            n = rng.randint(5, 200)
            g = random_graph(rng, n, rng.randint(n, 4 * n))
            ref = dijkstra(g, 0)
            h = constant_degree(g)
            for alg in ALGORITHMS:
                with self.subTest(algorithm=alg.__name__):
                    dist = alg(h, 0)
                    dist = {v: d for v, d in dist.items() if not isinstance(v, AuxVertex)}
                    self.assertEqual(count_dist_errors(ref, dist), 0)

    def test_unreachable_vertices(self):
        g = Graph()
        g.add_edge(0, 1, 5)
        g.add_edge(2, 3, 1)
        self.assertEqual(dijkstra(g, 0), {0: 0.0, 1: 5})
        self.check(g)


class TestShortestPath(unittest.TestCase):

    def assert_valid_paths(self, g, original, source=0):
        """Para cada vértice alcançado do grafo original, o caminho
        reconstruído deve começar na origem, usar arestas existentes no grafo
        original e ter custo igual à distância do Dijkstra."""
        weight = {}
        for u in original.adj:
            for v, w in original.adj[u]:
                weight[(u, v)] = min(w, weight.get((u, v), float('inf')))
        ref = dijkstra(original, source)
        for alg in ALGORITHMS:
            with self.subTest(algorithm=alg.__name__):
                dist, pred = alg(g, source, return_pred=True)
                self.assertEqual(count_dist_errors(ref, {v: dist[v] for v in ref}), 0)
                for v, d in ref.items():
                    path = shortest_path(pred, source, v)
                    self.assertEqual(path[0], source)
                    self.assertEqual(path[-1], v)
                    cost = sum(weight[(a, b)] for a, b in zip(path, path[1:]))
                    self.assertAlmostEqual(cost, d)

    def test_random_graphs(self):
        rng = random.Random(3)
        for _ in range(300):
            n = rng.randint(5, 200)
            g = random_graph(rng, n, rng.randint(n, 4 * n))
            self.assert_valid_paths(g, g)

    def test_random_graphs_bounded_degree(self):
        # Os vértices auxiliares "u#k" são removidos do caminho, que deve
        # então ser válido no grafo original
        rng = random.Random(4)
        for _ in range(100):
            n = rng.randint(5, 200)
            g = random_graph(rng, n, rng.randint(n, 4 * n))
            self.assert_valid_paths(bounded_out_degree(g, 2), g)

    def test_random_graphs_constant_degree(self):
        rng = random.Random(6)
        for _ in range(100):
            n = rng.randint(5, 200)
            g = random_graph(rng, n, rng.randint(n, 4 * n))
            self.assert_valid_paths(constant_degree(g), g)

    def test_unreachable_and_source(self):
        g = Graph()
        g.add_edge(0, 1, 5)
        g.add_edge(2, 3, 1)
        _, pred = sssp_duan_et_al_opt(g, 0, return_pred=True)
        self.assertEqual(shortest_path(pred, 0, 0), [0])
        self.assertEqual(shortest_path(pred, 0, 1), [0, 1])
        self.assertIsNone(shortest_path(pred, 0, 3))


class TestConstantDegree(unittest.TestCase):

    def test_degrees_at_most_two(self):
        rng = random.Random(8)
        g = random_graph(rng, 300, 1500)
        h = constant_degree(g)
        indeg = {}
        for u, edges in h.adj.items():
            self.assertLessEqual(len(edges), 2)
            for v, _ in edges:
                indeg[v] = indeg.get(v, 0) + 1
        self.assertLessEqual(max(indeg.values()), 2)
        # O(m) vértices: um por par (vértice, vizinho)
        self.assertLessEqual(len(h.adj), 2 * sum(len(e) for e in g.adj.values()))

    def test_isolated_and_sink_vertices_kept(self):
        g = Graph()
        g.adj[5]
        g.add_edge(0, 1, 2)
        h = constant_degree(g)
        self.assertIn(5, h.adj)
        self.assertIn(1, h.adj)
        self.assertEqual(dijkstra(h, 0)[1], 2)


class TestCountDistErrors(unittest.TestCase):

    def test_missing_key_is_inf(self):
        self.assertEqual(count_dist_errors({0: 0, 1: float('inf')}, {0: 0}), 0)

    def test_extra_finite_key_is_error(self):
        self.assertEqual(count_dist_errors({0: 0}, {0: 0, 1: 3}), 1)


if __name__ == "__main__":
    unittest.main()
