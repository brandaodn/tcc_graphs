"""Verifica invariantes observáveis da fila durante execuções BMSSP.

Executar: python3 -m unittest discover -s tests -p 'test_queue_invariants.py' -v
A condição de BatchPrepend aqui é uma hipótese sobre ordenação global;
o artigo deve ser consultado para suas pré-condições formais.
"""
import unittest
from unittest.mock import patch

from graphs.batch_pq import BatchPQ, BatchPQFast
from graphs.graphs import Graph, dijkstra
from graphs.duan_et_al import sssp_duan_et_al
from graphs.duan_et_al_iter import sssp_duan_et_al_iter
from graphs.duan_et_al_opt import sssp_duan_et_al_opt


class TestQueueInvariants(unittest.TestCase):
    def test_arbitrary_prepend_counterexample(self):
        for queue_type in (BatchPQ, BatchPQFast):
            with self.subTest(queue=queue_type.__name__):
                top = (float("inf"),) * 3
                q = queue_type(M=1, B=top)
                q.batch_prepend([("a", (21, 0, 0))])
                q.batch_prepend([("b", (24, 0, 0))])
                self.assertEqual(q._d0[0].items[0][1], "b")
                self.assertGreater(q._d0[0].items[0][0], q._d0[1].items[0][0])

    def test_bmssp_path_fails_without_invalid_prepend_order(self):
        graph = Graph()
        for v in range(5):
            graph.adj[v] = []
        for u, v, w in [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]:
            graph.add_edge(u, v, w)

        calls = []
        originals = {}
        for queue_type in (BatchPQ, BatchPQFast):
            original = queue_type.batch_prepend
            originals[queue_type] = original

            def checked(queue, pairs, original=original):
                current = list(queue._key_val.values())
                candidates = [key for v, key in pairs
                              if v not in queue._key_val or key < queue._key_val[v]]
                if candidates and current:
                    calls.append((max(candidates), min(current)))
                return original(queue, pairs)

            with patch.object(queue_type, "batch_prepend", checked):
                algorithms = ((sssp_duan_et_al, sssp_duan_et_al_iter)
                              if queue_type is BatchPQ else (sssp_duan_et_al_opt,))
                for algorithm in algorithms:
                    algorithm(graph, 0)
        self.assertFalse(any(a > b for a, b in calls),
                         f"Prepend potencialmente fora de ordem: {calls}")


if __name__ == "__main__":
    unittest.main()
