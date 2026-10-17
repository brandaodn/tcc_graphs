"""Testes da semântica de TotalOrder.relax (BMSSP).

Executar:
    python3 -m unittest discover -s tests -p 'test_total_order.py' -v

O contrato testado é: accepted=True somente quando distância ou desempate
efetivamente melhora. O teste não modifica a implementação original.
"""
import math
import unittest
from collections import defaultdict

from graphs.batch_pq import TotalOrder


class TestTotalOrderRelax(unittest.TestCase):
    def setUp(self):
        self.order = TotalOrder()
        self.dist = defaultdict(lambda: math.inf)
        self.dist["s"] = 0
        self.order.rank("s")

    def test_strict_distance_improvement(self):
        accepted, key = self.order.relax("s", "v", 5, self.dist)
        self.assertTrue(accepted)
        self.assertEqual(self.dist["v"], 5)
        self.assertEqual(self.order.pred["v"], "s")
        self.assertEqual(key, self.order.key("v", self.dist))

    def test_worse_distance_rejected(self):
        self.order.relax("s", "v", 5, self.dist)
        accepted, key = self.order.relax("s", "v", 8, self.dist)
        self.assertFalse(accepted)
        self.assertEqual(self.dist["v"], 5)
        self.assertEqual(key, self.order.key("v", self.dist))

    def test_equal_distance_without_improvement_rejected(self):
        self.order.relax("s", "v", 5, self.dist)
        before = (self.dist["v"], self.order.hops["v"], self.order.pred["v"])
        accepted, key = self.order.relax("s", "v", 5, self.dist)
        self.assertFalse(
            accepted,
            "Empate sem melhora em saltos/predecessor deve retornar False; "
            "True pode causar reinserções repetidas na BatchPQ."
        )
        self.assertEqual(
            before, (self.dist["v"], self.order.hops["v"], self.order.pred["v"])
        )
        self.assertEqual(key, self.order.key("v", self.dist))

    def test_equal_distance_better_hops_accepted(self):
        self.order.relax("s", "a", 0, self.dist)
        self.order.relax("a", "v", 5, self.dist)
        self.order.relax("s", "v", 5, self.dist)
        self.assertEqual(self.order.hops["v"], 1)
        self.assertEqual(self.order.pred["v"], "s")

    def test_equal_distance_better_predecessor_rank(self):
        self.order.relax("s", "a", 0, self.dist)
        self.order.relax("s", "b", 0, self.dist)
        self.order.relax("b", "v", 5, self.dist)
        self.assertEqual(self.order.pred["v"], "b")
        accepted, _ = self.order.relax("a", "v", 5, self.dist)
        self.assertTrue(accepted)
        self.assertEqual(self.order.pred["v"], "a")

    def test_source_zero_cycle_not_accepted(self):
        accepted, _ = self.order.relax("s", "s", 0, self.dist)
        self.assertFalse(accepted, "Ciclo de peso zero não melhora a origem")
        self.assertEqual(self.dist["s"], 0)


if __name__ == "__main__":
    unittest.main()
