"""Testes de contrato das filas de prioridade usadas no BMSSP.

Executar:
    python3 -m unittest discover -s tests -p 'test_batch_pq.py' -v

Os testes exercitam BatchPQ e BatchPQFast sem alterar sua implementação.
Falhas podem revelar desvios da semântica esperada de Pull.
"""
import unittest

from graphs.batch_pq import BatchPQ, BatchPQFast

TOP = (float("inf"), float("inf"), float("inf"))


def key(distance, rank=0):
    return (distance, 0, rank)


class QueueContractMixin:
    QUEUE = None

    def new_queue(self, size=2):
        return self.QUEUE(M=size, B=TOP)

    def test_empty_queue(self):
        q = self.new_queue()
        self.assertTrue(q.is_empty())
        bound, batch = q.pull()
        self.assertEqual(bound, TOP)
        self.assertEqual(batch, [])

    def test_single_insert(self):
        q = self.new_queue()
        q.insert("a", key(3))
        bound, batch = q.pull()
        self.assertEqual(batch, ["a"])
        self.assertEqual(bound, TOP)
        self.assertTrue(q.is_empty())

    def test_pull_returns_smallest_keys(self):
        q = self.new_queue(size=2)
        for vertex, dist in (("c", 7), ("a", 1), ("d", 9), ("b", 3)):
            q.insert(vertex, key(dist))
        bound, batch = q.pull()
        self.assertEqual(batch, ["a", "b"])
        self.assertEqual(bound, key(7))
        self.assertFalse(q.is_empty())
        second_bound, second = q.pull()
        self.assertEqual(second, ["c", "d"])
        self.assertEqual(second_bound, TOP)
        self.assertTrue(q.is_empty())

    def test_decrease_key_keeps_only_current_entry(self):
        q = self.new_queue(size=2)
        q.insert("a", key(10))
        q.insert("b", key(6))
        q.insert("a", key(2))
        bound, batch = q.pull()
        self.assertEqual(batch, ["a", "b"])
        self.assertEqual(bound, TOP)
        self.assertTrue(q.is_empty())

    def test_larger_key_does_not_replace_smaller(self):
        q = self.new_queue()
        q.insert("a", key(2))
        q.insert("a", key(8))
        _, batch = q.pull()
        self.assertEqual(batch, ["a"])
        self.assertTrue(q.is_empty())

    def test_batch_prepend_and_insert_global_order(self):
        q = self.new_queue(size=2)
        q.insert("d", key(8))
        q.insert("c", key(6))
        q.batch_prepend([("b", key(3)), ("a", key(1))])
        bound, batch = q.pull()
        self.assertEqual(batch, ["a", "b"])
        self.assertEqual(bound, key(6))
        _, remaining = q.pull()
        self.assertEqual(remaining, ["c", "d"])

    def test_duplicate_batch_keys(self):
        q = self.new_queue(size=2)
        q.batch_prepend([("a", key(8)), ("a", key(2)), ("b", key(4))])
        bound, batch = q.pull()
        self.assertEqual(batch, ["a", "b"])
        self.assertEqual(bound, TOP)
        self.assertTrue(q.is_empty())

    def test_stale_prefix_must_not_look_empty(self):
        # Duas entradas desatualizadas antecedem a entrada vigente de 'a'.
        # Pull nao pode retornar [] enquanto _key_val ainda tem elementos.
        q = self.new_queue(size=1)
        q.batch_prepend([("a", key(9))])
        q.batch_prepend([("a", key(7))])
        q.insert("a", key(2))
        self.assertFalse(q.is_empty())
        bound, batch = q.pull()
        self.assertEqual(batch, ["a"])
        self.assertEqual(bound, TOP)
        self.assertTrue(q.is_empty())

    def test_no_phantom_items_after_decreases(self):
        q = self.new_queue(size=1)
        q.insert("a", key(10))
        q.insert("a", key(8))
        q.insert("a", key(6))
        q.insert("a", key(4))
        q.insert("a", key(2))
        self.assertEqual(q.pull()[1], ["a"])
        self.assertTrue(q.is_empty())
        self.assertEqual(q.pull(), (TOP, []))


class TestBatchPQ(QueueContractMixin, unittest.TestCase):
    QUEUE = BatchPQ


class TestBatchPQFast(QueueContractMixin, unittest.TestCase):
    QUEUE = BatchPQFast


if __name__ == "__main__":
    unittest.main()
