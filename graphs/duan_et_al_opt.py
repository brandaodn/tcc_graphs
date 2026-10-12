"""BMSSP com BatchPQ otimizada.

Mantém a lógica de BMSSP / find_pivots / base_case de duan_et_al.py; troca
apenas a estrutura D (Lema 3.3), que era o gargalo:

  * insert: bisect.insort no bloco (O(log M) comparações + memmove) em vez de
    append + sort completo; lista paralela de limites superiores (`_d1_up`)
    em vez de reconstruí-la a cada chamada.
  * valores maiores que todos os limites entram no ÚLTIMO bloco (como no
    artigo, cujo último bloco tem limite B) em vez de criar um bloco novo
    de 1 elemento a cada inserção crescente.
  * pull: remoção preguiçosa; só reescreve os blocos do prefixo visitado,
    em vez de varrer todos os blocos de D.
"""
import bisect
import math
from collections import defaultdict

from graphs.duan_et_al import (
    INF, TotalOrder, _Block, base_case, find_pivots,
)


class BatchPQFast:
    def __init__(self, M: int, B):
        assert M >= 1
        self.M = M
        self.B = B
        self._d0: list[_Block] = []
        self._d1: list[_Block] = []
        self._d1_up: list[tuple] = []     # _d1_up[i] == _d1[i].upper
        self._key_val: dict = {}          # vértice -> chave vigente

    # ------------------------------------------------------------------
    def insert(self, vertex, key):
        cur = self._key_val.get(vertex)
        if cur is not None and key >= cur:
            return
        self._key_val[vertex] = key
        d1, up = self._d1, self._d1_up
        if not d1:
            b = _Block()
            b.items = [(key, vertex)]
            b.upper = key
            d1.append(b)
            up.append(key)
            return
        idx = bisect.bisect_left(up, key)
        if idx == len(d1):                 # maior que tudo: último bloco
            idx -= 1
        block = d1[idx]
        bisect.insort(block.items, (key, vertex))
        last = block.items[-1][0]
        block.upper = last
        up[idx] = last
        if len(block.items) > self.M:
            right = block.split()
            up[idx] = block.upper
            d1.insert(idx + 1, right)
            up.insert(idx + 1, right.upper)

    # ------------------------------------------------------------------
    def batch_prepend(self, pairs):
        if not pairs:
            return
        deduped: dict = {}
        for vertex, key in pairs:
            if vertex not in deduped or key < deduped[vertex]:
                deduped[vertex] = key
        filtered = []
        kv = self._key_val
        for vertex, key in deduped.items():
            cur = kv.get(vertex)
            if cur is not None and key >= cur:
                continue
            kv[vertex] = key
            filtered.append((key, vertex))
        if not filtered:
            return
        filtered.sort()
        L = len(filtered)
        if L <= self.M:
            b = _Block()
            b.push_sorted(filtered)
            self._d0.insert(0, b)
        else:
            chunk = max(1, self.M // 2)
            new_blocks = []
            for i in range(0, L, chunk):
                b = _Block()
                b.push_sorted(filtered[i: i + chunk])
                new_blocks.append(b)
            self._d0[0:0] = new_blocks

    # ------------------------------------------------------------------
    def _collect(self, seq, limit):
        """Coleta itens VÁLIDOS dos primeiros blocos até `limit`.
        Devolve (itens, nº de blocos visitados)."""
        out = []
        kv = self._key_val
        visited = 0
        for block in seq:
            visited += 1
            for pair in block.items:
                if kv.get(pair[1]) == pair[0]:
                    out.append(pair)
            if len(out) >= limit:
                break
        return out, visited

    def _compact(self, seq, visited, with_up):
        """Remove itens obsoletos/puxados apenas dos `visited` primeiros
        blocos e descarta os que ficarem vazios."""
        kv = self._key_val
        keep = []
        for i in range(visited):
            b = seq[i]
            b.items = [p for p in b.items if kv.get(p[1]) == p[0]]
            if b.items:
                b.upper = b.items[-1][0]
                keep.append(b)
        seq[0:visited] = keep
        if with_up:
            self._d1_up[:] = [b.upper for b in seq]

    def pull(self):
        c0, v0 = self._collect(self._d0, self.M)
        c1, v1 = self._collect(self._d1, self.M)
        candidates = c0 + c1
        if not candidates:
            return self.B, []
        candidates.sort()
        seen = set()
        valid = []
        for key, vertex in candidates:
            if vertex in seen:
                continue
            seen.add(vertex)
            valid.append(vertex)
            if len(valid) == self.M:
                break
        kv = self._key_val
        for vertex in valid:
            del kv[vertex]
        self._compact(self._d0, v0, False)
        self._compact(self._d1, v1, True)
        return self._min_remaining_val(), valid

    def _min_remaining_val(self):
        mins = []
        if self._d0:
            mins.append(self._d0[0].items[0][0])
        if self._d1:
            mins.append(self._d1[0].items[0][0])
        return min(mins) if mins else self.B

    def is_empty(self) -> bool:
        return not self._key_val


# =============================================================================
def BMSSP_opt(graph, l, B_key, S, db, k, t, order: TotalOrder):
    if l == 0:
        return base_case(graph, next(iter(S)), B_key, db, k, order)

    P, W = find_pivots(graph, S, B_key, db, k, order)
    D = BatchPQFast(M=2 ** ((l - 1) * t), B=B_key)
    for x in P:
        D.insert(x, order.key(x, db))

    B_prime = min((order.key(x, db) for x in P), default=B_key)
    U = set()
    limit = (k ** 2) * (2 ** (l * t))

    while len(U) < limit and not D.is_empty():
        Bi, Si = D.pull()
        if not Si:
            break
        B_i_prime, Ui = BMSSP_opt(graph, l - 1, Bi, set(Si), db, k, t, order)
        U |= Ui

        K = []
        for u in Ui:
            for v, w in graph.adj[u]:
                accepted, key_v = order.relax(u, v, w, db)
                if accepted:
                    if Bi <= key_v < B_key:
                        D.insert(v, key_v)
                    elif B_i_prime <= key_v < Bi:
                        K.append((v, key_v))
        K += [(x, order.key(x, db)) for x in Si
              if B_i_prime <= order.key(x, db) < Bi]
        D.batch_prepend(K)
        B_prime = min(B_i_prime, B_key)

    U |= {x for x in W if order.key(x, db) < B_prime}
    return B_prime, U


def sssp_duan_et_al_opt(graph, source):
    db = defaultdict(lambda: INF)
    db[source] = 0
    order = TotalOrder()
    order.rank(source)
    n = len(graph.adj)
    k = max(2, int(math.log2(n) ** (1 / 3))) if n > 1 else 2
    t = max(2, int(math.log2(n) ** (2 / 3))) if n > 1 else 2
    l = int(math.log2(n) / t) + 1 if n > 1 else 1
    BMSSP_opt(graph, l, order.TOP, {source}, db, k, t, order)
    return dict(db)



