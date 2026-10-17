import bisect
from collections import defaultdict

INF = float('inf')


class TotalOrder:
    def __init__(self):
        self.hops = defaultdict(int)
        self._rank = {}
        self._counter = 0
        # Sentinela maior que qualquer chave real — usado para B=infinito
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
        return False, self.key(v, db)


class _Block:
    def __init__(self):
        self.items: list[tuple[tuple, object]] = []
        self.upper = None  # Definido externamente (sentinela TOP)

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
    """Estrutura de dados D do Lema 3.3, com valores sendo chaves totalmente
    ordenadas (db, hops, rank)."""

    def __init__(self, M: int, B):
        assert M >= 1
        self.M = M
        self.B = B
        self._d0: list[_Block] = []   # blocos de BatchPrepend
        self._d1: list[_Block] = []   # blocos de Insert
        self._key_val: dict = {}       # vértice -> menor chave atualmente na estrutura

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


class BatchPQFast:
    """Implementação otimizada de BatchPQ com remoção preguiçosa e bisect.insort."""

    def __init__(self, M: int, B):
        assert M >= 1
        self.M = M
        self.B = B
        self._d0: list[_Block] = []
        self._d1: list[_Block] = []
        self._d1_up: list[tuple] = []     # _d1_up[i] == _d1[i].upper
        self._key_val: dict = {}          # vértice -> chave vigente

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

    def _collect(self, seq, limit):
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
