"""Diagnostic queue-equivalence checks under a conservative BatchPrepend precondition.

The condition checked here (every prepended key below all active keys) is
sufficient for this experiment, but it is not a proof that all formal
preconditions of the Duan et al. structure are satisfied.

Run: python -m unittest discover -s tests -p 'test_queue_legal_prepend.py' -v
"""
import heapq
import itertools
import math
import random
import unittest

from graphs.batch_pq import BatchPQ


class LazyHeapQueue:
    def __init__(self, M, B):
        self.M, self.B = M, B
        self._key_val = {}
        self._heap = []
        self._serial = itertools.count()

    def insert(self, vertex, key):
        previous = self._key_val.get(vertex)
        if previous is not None and key >= previous:
            return
        self._key_val[vertex] = key
        heapq.heappush(self._heap, (key, next(self._serial), vertex))

    def batch_prepend(self, pairs):
        for vertex, key in pairs:
            self.insert(vertex, key)

    def pull(self):
        batch = []
        while len(batch) < self.M:
            while self._heap and self._key_val.get(self._heap[0][2]) != self._heap[0][0]:
                heapq.heappop(self._heap)
            if not self._heap:
                break
            key, _, vertex = heapq.heappop(self._heap)
            if self._key_val.get(vertex) == key:
                del self._key_val[vertex]
                batch.append(vertex)
        while self._heap and self._key_val.get(self._heap[0][2]) != self._heap[0][0]:
            heapq.heappop(self._heap)
        return (self._heap[0][0] if self._heap else self.B), batch


class QueueLegalPrependTests(unittest.TestCase):
    def test_batches_and_boundaries_agree_with_reference_heap(self):
        rng = random.Random(20262026)
        pulls = 0
        for trial in range(500):
            M = rng.choice((1, 2, 4, 8))
            B = (math.inf, math.inf, math.inf)
            actual, reference = BatchPQ(M, B), LazyHeapQueue(M, B)
            vertex_counter = 0
            for step in range(100):
                active = list(actual._key_val.values())
                minimum = min(active) if active else (100000, 0, 0)
                choice = rng.random()
                if choice < .3 and active and minimum[0] > 0:
                    pairs = []
                    for _ in range(rng.randrange(1, 5)):
                        vertex_counter += 1
                        pairs.append((
                            vertex_counter,
                            (rng.randrange(0, minimum[0]), 0, vertex_counter),
                        ))
                    actual.batch_prepend(pairs)
                    reference.batch_prepend(pairs)
                elif choice < .72:
                    vertex_counter += 1
                    vertex = vertex_counter
                    key = (rng.randrange(200, 400), 0, vertex)
                    actual.insert(vertex, key)
                    reference.insert(vertex, key)
                else:
                    actual_bound, actual_batch = actual.pull()
                    reference_bound, reference_batch = reference.pull()
                    pulls += 1
                    self.assertEqual(
                        set(actual_batch), set(reference_batch),
                        f"trial={trial} step={step} M={M}"
                    )
                    self.assertEqual(
                        actual_bound, reference_bound,
                        f"trial={trial} step={step} M={M}"
                    )
                self.assertEqual(actual._key_val, reference._key_val)
        self.assertGreater(pulls, 10000)


if __name__ == "__main__":
    unittest.main()
