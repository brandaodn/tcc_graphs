"""Fila de referência diagnóstica com fronteira global exata.

Destinada APENAS a testes funcionais. A complexidade de pull é O(N log N);
não preserva a garantia assintótica reivindicada para BatchPQ.
"""
from graphs.batch_pq import BatchPQ


class BatchPQReference(BatchPQ):
    def pull(self):
        if not self._key_val:
            return self.B, []
        selected = sorted(
            self._key_val.items(), key=lambda item: (item[1], repr(item[0]))
        )[:self.M]
        vertices = [v for v, _ in selected]
        for v in vertices:
            del self._key_val[v]
        # A representacao por blocos nao é necessária ao oráculo; limpe
        # itens removidos e obsoletos para preservar consistência observável.
        live = dict(self._key_val)
        for seq in (self._d0, self._d1):
            for block in seq:
                block.items = [
                    (k, v) for k, v in block.items
                    if live.get(v) == k
                ]
                if block.items:
                    block.upper = block.items[-1][0]
        self._d0 = [b for b in self._d0 if b.items]
        self._d1 = [b for b in self._d1 if b.items]
        boundary = min(live.values(), default=self.B)
        return boundary, vertices
