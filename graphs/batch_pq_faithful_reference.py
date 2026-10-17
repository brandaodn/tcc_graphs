"""Correctness-first reference for the BMSSP bounded-batch queue.

This implementation deliberately uses global sorting and does NOT achieve
Lemma 3.3's amortized complexity. It is a functional oracle for validating
the optimized data structure and the recursive algorithm.
"""
class BatchPQFaithfulReference:
    def __init__(self, M, B):
        if M < 1:
            raise ValueError("M must be >= 1")
        self.M, self.B = M, B
        self._key_val = {}

    def insert(self, vertex, key):
        if key >= self.B:
            return
        previous = self._key_val.get(vertex)
        if previous is None or key < previous:
            self._key_val[vertex] = key

    def batch_prepend(self, pairs):
        items = list(pairs)
        if self._key_val and items:
            smallest_existing = min(self._key_val.values())
            if any(key >= smallest_existing for _, key in items):
                raise ValueError("BatchPrepend requires keys below current minimum")
        for vertex, key in items:
            self.insert(vertex, key)

    def pull(self):
        if not self._key_val:
            return self.B, []
        ordered = sorted(self._key_val.items(), key=lambda p: p[1])
        selected = ordered[:self.M]
        for vertex, _ in selected:
            del self._key_val[vertex]
        boundary = ordered[len(selected)][1] if len(ordered) > len(selected) else self.B
        return boundary, [vertex for vertex, _ in selected]

    def is_empty(self):
        return not self._key_val
