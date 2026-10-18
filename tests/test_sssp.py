"""Testes de corretude: cada implementação do BMSSP deve produzir as mesmas
distâncias que o Dijkstra.

Executar a partir da raiz do repositório:
    python -m unittest discover tests
"""
import random
import unittest

from graphs import (
    Graph,
    dijkstra,
    count_dist_errors,
    bounded_out_degree,
    sssp_duan_et_al,
    sssp_duan_et_al_iter,
    sssp_duan_et_al_opt,
)

ALGORITHMS = (sssp_duan_et_al, sssp_duan_et_al_iter, sssp_duan_et_al_opt)


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

    def test_unreachable_vertices(self):
        g = Graph()
        g.add_edge(0, 1, 5)
        g.add_edge(2, 3, 1)
        self.assertEqual(dijkstra(g, 0), {0: 0.0, 1: 5})
        self.check(g)


class TestCountDistErrors(unittest.TestCase):

    def test_missing_key_is_inf(self):
        self.assertEqual(count_dist_errors({0: 0, 1: float('inf')}, {0: 0}), 0)

    def test_extra_finite_key_is_error(self):
        self.assertEqual(count_dist_errors({0: 0}, {0: 0, 1: 3}), 1)


if __name__ == "__main__":
    unittest.main()
