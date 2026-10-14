import math
from collections import defaultdict
from graphs.batch_pq import INF, TotalOrder, BatchPQFast
from graphs.duan_et_al import base_case, find_pivots


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
