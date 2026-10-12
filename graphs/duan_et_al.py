import heapq
import math
import bisect
from collections import defaultdict
from graphs.graphs import Graph, dijkstra

INF = float('inf')

class TotalOrder:
    def __init__(self):
        self.hops = defaultdict(int)
        self._rank = {}
        self._counter = 0
        # sentinela maior que qualquer chave real — usado para B=infinito
        self.TOP = (INF, INF, INF)
        self.pred = {}

    def rank(self, v):
        r = self._rank.get(v)
        if r is None:
            r = self._counter
            self._counter += 1
            self._rank[v] = r
        return r

    def key(self, v, db):
        return (db[v], self.hops[v], self.rank(v))

    def relax(self, u, v, w, db):
        """Tenta relaxar a aresta (u,v) respeitando a ordem total de caminhos
        (distância, saltos, rank do predecessor). Retorna (aceito, nova_chave)."""
        nova_dist = db[u] + w
        nova_hops = self.hops[u] + 1
        old_dist = db[v]
        old_hops = self.hops[v]

        if nova_dist < old_dist:
            db[v] = nova_dist
            self.hops[v] = nova_hops
            self.pred[v] = u
            return True, self.key(v, db)
        elif nova_dist == old_dist:
            cand_tie = (nova_hops, self.rank(u))
            old_tie = (old_hops, self.rank(self.pred.get(v, v)))
            if cand_tie < old_tie:
                self.hops[v] = nova_hops
                self.pred[v] = u
            return True, self.key(v, db)
        return False, self.key(v, db)




class _Block:
    def __init__(self):
        self.items: list[tuple[tuple, object]] = []
        self.upper = None  # definido externamente (sentinela TOP)

    def push_sorted(self, pairs):
        self.items = pairs
        self.upper = pairs[-1][0] if pairs else None

    def split(self) -> "_Block":
        mid = len(self.items) // 2
        right = _Block()
        right.push_sorted(self.items[mid:])
        self.push_sorted(self.items[:mid])
        return right

    def __len__(self):
        return len(self.items)


class BatchPQ:
    """
    Estrutura de dados D do Lema 3.3, com valores sendo CHAVES totalmente
    ordenadas (db, hops, rank) em vez de floats simples.

    Parâmetros
    ----------
    M : int   — tamanho de bloco e quantidade de itens por Pull
    B : tuple — upper-bound global (chave, retornada pelo Pull quando vazio)
    """

    def __init__(self, M: int, B):
        assert M >= 1
        self.M = M
        self.B = B
        self._d0: list[_Block] = []   # blocos de BatchPrepend
        self._d1: list[_Block] = []   # blocos de Insert
        self._key_val: dict = {}       # vertice -> menor chave atualmente na estrutura

    # ------------------------------------------------------------------
    def insert(self, vertex, key):
        """Insert: O(max{1, log(N/M)}) amortizado."""
        if vertex in self._key_val and key >= self._key_val[vertex]:
            return
        self._key_val[vertex] = key
        block = self._find_or_create_d1_block(key)
        block.items.append((key, vertex))
        block.items.sort(key=lambda p: p[0])
        block.upper = block.items[-1][0]
        if len(block) > self.M:
            self._split_d1_block(block)

    def _find_or_create_d1_block(self, key) -> _Block:
        uppers: list[tuple] = []
        for block in self._d1:
            if block.upper is not None:
                uppers.append(block.upper)
        idx = bisect.bisect_left(uppers, key)
        if idx < len(self._d1):
            return self._d1[idx]
        b = _Block()
        b.upper = self.B
        self._d1.append(b)
        return b

    def _split_d1_block(self, block: _Block):
        idx = self._d1.index(block)
        right = block.split()
        self._d1.insert(idx + 1, right)

    # ------------------------------------------------------------------
    def batch_prepend(self, pairs: list[tuple[object, tuple]]):
        """BatchPrepend: O(|L| · max{1, log(|L|/M)}) amortizado."""
        if not pairs:
            return
        deduped: dict = {}
        for vertex, key in pairs:
            if vertex not in deduped or key < deduped[vertex]:
                deduped[vertex] = key
        filtered = []
        for vertex, key in deduped.items():
            if vertex in self._key_val and key >= self._key_val[vertex]:
                continue
            self._key_val[vertex] = key
            filtered.append((key, vertex))
        if not filtered:
            return
        filtered.sort(key=lambda p: p[0])
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
    def pull(self):
        """Pull: retorna (x, S') com |S'| <= M, x = chave-limite."""
        candidates = []
        self._collect_prefix(self._d0, candidates, self.M)
        self._collect_prefix(self._d1, candidates, self.M)
        if not candidates:
            return self.B, []
        candidates.sort(key=lambda p: p[0])
        valid = []
        seen = set()
        for key, vertex in candidates:
            if vertex in seen:
                continue
            seen.add(vertex)
            if self._key_val.get(vertex, self.B) < key:
                continue   # lazy deletion
            valid.append((key, vertex))
            if len(valid) == self.M:
                break
        if not valid:
            return self.B, []
        pulled = {vertex for _, vertex in valid}
        self._remove_keys(pulled)
        for vertex in pulled:
            del self._key_val[vertex]
        x = self._min_remaining_val()
        return x, [vertex for _, vertex in valid]

    def _collect_prefix(self, seq, out, limit):
        collected = 0
        for block in seq:
            for pair in block.items:
                out.append(pair)
                collected += 1
            if collected >= limit:
                break

    def _remove_keys(self, vertices: set):
        for seq in (self._d0, self._d1):
            for block in seq:
                block.items = [(k, v) for k, v in block.items if v not in vertices]
                if block.items:
                    block.upper = block.items[-1][0]
        self._d0 = [b for b in self._d0 if b.items]
        self._d1 = [b for b in self._d1 if b.items]

    def _min_remaining_val(self):
        mins = []
        if self._d0 and self._d0[0].items:
            mins.append(self._d0[0].items[0][0])
        if self._d1 and self._d1[0].items:
            mins.append(self._d1[0].items[0][0])
        return min(mins) if mins else self.B

    def is_empty(self) -> bool:
        return not self._key_val

# =============================================================================
# base_case (Algoritmo 2) — usa chaves em vez de db[] puro
# =============================================================================

def base_case(graph, s, B_key, db, k, order: TotalOrder):
    U0 = set()
    heap = [(order.key(s, db), s)]
    while heap and len(U0) < k + 1:
        key_u, u = heapq.heappop(heap)
        if u in U0:
            continue
        U0.add(u)
        for v, w in graph.adj[u]:
            accepted, key_v = order.relax(u, v, w, db)
            if accepted and key_v < B_key:
                heapq.heappush(heap, (key_v, v))
    if len(U0) <= k:
        return B_key, U0
    max_key = max(order.key(v, db) for v in U0)
    U = {v for v in U0 if order.key(v, db) < max_key}
    return max_key, U




def find_pivots(graph, S, B_key, db, k, order: TotalOrder):
    W = set(S)
    Wi_prev = set(S)
    for i in range(k):
        Wi = set()
        for u in Wi_prev:
            for v, w in graph.adj[u]:
                accepted, key_v = order.relax(u, v, w, db)
                if accepted and key_v < B_key:
                    Wi.add(v)
        W |= Wi
        Wi_prev = Wi
        if len(W) > k * len(S):
            return set(S), W
    parent = {v: order.pred[v] for v in W if v in order.pred and order.pred[v] in W}
    roots = {u for u in S if u not in parent}
    children = defaultdict(list)
    for v, p in parent.items():
        children[p].append(v)

    def count_subtree(root):
        count = 0
        stack = [root]
        visited = set()
        while stack:
            x = stack.pop()
            if x in visited:
                continue
            visited.add(x)
            count += 1
            for v in children.get(x, []):
                stack.append(v)
        return count

    P = set()
    for u in roots:
        if count_subtree(u) >= k:
            P.add(u)
    return P, W




def BMSSP(graph, l, B_key, S, db, k, t, order: TotalOrder):

    if l == 0:
        return base_case(graph, next(iter(S)), B_key, db, k, order)

    P, W = find_pivots(graph, S, B_key, db, k, order)

    M = 2 ** ((l - 1) * t)

    D = BatchPQ(M=M, B=B_key)

    for x in P:
        D.insert(x, order.key(x, db))

    B_prime = min((order.key(x, db) for x in P), default=B_key)
    U = set()

    while len(U) < (k ** 2) * (2 ** (l * t)) and not D.is_empty():

        Bi, Si = D.pull()

        if not Si:
            break

        B_i_prime, Ui = BMSSP(graph, l - 1, Bi, set(Si), db, k, t, order)

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

        prepend_items = K + [
            (x, order.key(x, db)) for x in Si
            if B_i_prime <= order.key(x, db) < Bi
        ]
        D.batch_prepend(prepend_items)

        B_prime = min(B_i_prime, B_key)

    U |= {x for x in W if order.key(x, db) < B_prime}
    return B_prime, U


# =============================================================================
# sssp_duan_et_al
# =============================================================================

def sssp_duan_et_al(graph, source):
    db = defaultdict(lambda: INF)
    db[source] = 0
    order = TotalOrder()
    order.rank(source)  # garante que a fonte tenha o menor rank possível
    n = len(graph.adj)
    k = max(2, int(math.log2(n) ** (1 / 3))) if n > 1 else 2
    t = max(2, int(math.log2(n) ** (2 / 3))) if n > 1 else 2
    l = int(math.log2(n) / t) + 1 if n > 1 else 1
    BMSSP(graph, l, order.TOP, {source}, db, k, t, order)

    return dict(db)
