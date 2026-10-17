import heapq
import math
from collections import defaultdict
from graphs.graphs import Graph, dijkstra
from graphs.batch_pq import INF, TotalOrder, _Block, BatchPQ


def base_case(graph, s, B_key, db, k, order: TotalOrder):
    U0 = set()
    heap = [(order.key(s, db), s)]
    while heap and len(U0) < k + 1:
        key_u, u = heapq.heappop(heap)
        if u in U0:
            continue
        # Ignora entradas antigas produzidas antes de uma melhoria de chave.
        # Nao finaliza um vertice usando um rotulo obsoleto.
        if key_u != order.key(u, db):
            continue
        U0.add(u)
        for v, w in graph.adj[u]:
            accepted, key_v = order.relax(u, v, w, db)
            # Um rotulo ja conhecido ainda pode precisar ser explorado.
            # A fila e U0 evitam processamento repetido dos vertices finalizados.
            if key_v < B_key and v not in U0:
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
                # A exploracao deve incluir vertices com rotulos ja conhecidos:
                # accepted informa apenas se houve melhora nesta relaxacao.
                # Evita reintroduzir vertices fora do limite B_key.
                if key_v < B_key:
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


def sssp_duan_et_al(graph, source):
    db = defaultdict(lambda: INF)
    db[source] = 0
    order = TotalOrder()
    order.rank(source)
    n = len(graph.adj)
    k = max(2, int(math.log2(n) ** (1 / 3))) if n > 1 else 2
    t = max(2, int(math.log2(n) ** (2 / 3))) if n > 1 else 2
    l = int(math.log2(n) / t) + 1 if n > 1 else 1
    BMSSP(graph, l, order.TOP, {source}, db, k, t, order)
    return dict(db)
