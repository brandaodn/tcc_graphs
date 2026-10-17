"""Testes aleatorios reproduziveis das duas filas contra um oraculo simples.

python3 -m unittest discover -s tests -p 'test_batch_pq_random.py' -v
"""
import random
import unittest
from graphs.batch_pq import BatchPQ, BatchPQFast

TOP = (float("inf"),) * 3


def key(n):
    return (n, 0, 0)


class ReferenceQueue:
    def __init__(self, m):
        self.m = m
        self.items = {}

    def insert(self, v, k):
        if v not in self.items or k < self.items[v]:
            self.items[v] = k

    def batch_prepend(self, pairs):
        for v, k in pairs:
            self.insert(v, k)

    def pull(self):
        chosen = sorted(self.items, key=lambda v: (self.items[v], v))[:self.m]
        for v in chosen:
            del self.items[v]
        boundary = min(self.items.values(), default=TOP)
        return boundary, chosen


class TestRandomizedQueue(unittest.TestCase):
    def test_sequences_against_reference(self):
        for implementation in (BatchPQ, BatchPQFast):
            for seed in range(20):
                rng = random.Random(20261017 + seed)
                m = rng.choice((1, 2, 3, 5, 8))
                actual = implementation(M=m, B=TOP)
                reference = ReferenceQueue(m)
                history = []
                for step in range(150):
                    roll = rng.random()
                    if roll < 0.45:
                        v, k = rng.randrange(18), key(rng.randrange(50))
                        actual.insert(v, k)
                        reference.insert(v, k)
                        history.append(("insert", v, k))
                    elif roll < 0.75:
                        pairs = [(rng.randrange(18), key(rng.randrange(50)))
                                 for _ in range(rng.randint(1, 9))]
                        actual.batch_prepend(pairs)
                        reference.batch_prepend(pairs)
                        history.append(("prepend", pairs))
                    else:
                        expected_boundary, expected_vertices = reference.pull()
                        observed_boundary, observed_vertices = actual.pull()
                        history.append(("pull",))
                        details = (f"queue={implementation.__name__}, seed={seed}, "
                                   f"step={step}, m={m}, recent={history[-15:]}")
                        self.assertEqual(set(observed_vertices), set(expected_vertices), details)
                        self.assertEqual(observed_boundary, expected_boundary, details)
                    self.assertEqual(actual.is_empty(), not reference.items,
                                     f"{implementation.__name__}, seed={seed}, step={step}")


if __name__ == "__main__":
    unittest.main()
