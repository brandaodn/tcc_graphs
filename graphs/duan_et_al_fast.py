"""BMSSP com representação de baixo custo para Python ("melhor caso").

Mesmo algoritmo de duan_et_al_opt (mesmos passos, BatchPQFast e ordem total
de caminhos), mudando apenas a representação:
- vértices renumerados para 0..N-1 e adjacência em lista de listas;
- db, hops e pred em listas em vez de defaultdict/dict;
- relaxamento escrito diretamente nos laços, sem chamadas de método;
- o desempate da ordem total usa o próprio índice do vértice como rank
  (qualquer rótulo injetivo serve, como em TotalOrder.rank).

A conversão do grafo está incluída no tempo de sssp_duan_et_al_fast.
"""
import heapq
import math
from collections import defaultdict
from graphs.batch_pq import INF, BatchPQFast

TOP = (INF, INF, INF)


def _base_case(adj, s, B, db, hops, pred, k):
    U0 = set()
    heap = [((db[s], hops[s], s), s)]
    while heap and len(U0) < k + 1:
        _, u = heapq.heappop(heap)
        if u in U0:
            continue
        U0.add(u)
        du, hu = db[u], hops[u] + 1
        for v, w in adj[u]:
            nd = du + w
            dv = db[v]
            if nd < dv:
                db[v] = nd; hops[v] = hu; pred[v] = u
            elif nd == dv:
                p = pred[v]
                if (hu, u) < (hops[v], v if p < 0 else p):
                    hops[v] = hu; pred[v] = u
            else:
                continue
            key_v = (db[v], hops[v], v)
            if key_v < B:
                heapq.heappush(heap, (key_v, v))
    if len(U0) <= k:
        return B, U0
    max_key = max((db[v], hops[v], v) for v in U0)
    return max_key, {v for v in U0 if (db[v], hops[v], v) < max_key}


def _find_pivots(adj, S, B, db, hops, pred, k):
    W = set(S)
    Wi_prev = set(S)
    for _ in range(k):
        Wi = set()
        for u in Wi_prev:
            du, hu = db[u], hops[u] + 1
            for v, w in adj[u]:
                nd = du + w
                dv = db[v]
                if nd < dv:
                    db[v] = nd; hops[v] = hu; pred[v] = u
                elif nd == dv:
                    p = pred[v]
                    if (hu, u) < (hops[v], v if p < 0 else p):
                        hops[v] = hu; pred[v] = u
                else:
                    continue
                if (db[v], hops[v], v) < B:
                    Wi.add(v)
        W |= Wi
        Wi_prev = Wi
        if len(W) > k * len(S):
            return set(S), W
    children = defaultdict(list)
    has_parent = set()
    for v in W:
        p = pred[v]
        if p >= 0 and p in W:
            children[p].append(v)
            has_parent.add(v)

    P = set()
    for root in S:
        if root in has_parent:
            continue
        count = 0
        stack = [root]
        visited = set()
        while stack:
            x = stack.pop()
            if x in visited:
                continue
            visited.add(x)
            count += 1
            stack.extend(children.get(x, ()))
        if count >= k:
            P.add(root)
    return P, W


def _bmssp(adj, l, B, S, db, hops, pred, k, t):
    if l == 0:
        return _base_case(adj, next(iter(S)), B, db, hops, pred, k)

    P, W = _find_pivots(adj, S, B, db, hops, pred, k)
    D = BatchPQFast(M=2 ** ((l - 1) * t), B=B)
    for x in P:
        D.insert(x, (db[x], hops[x], x))

    B_prime = min(((db[x], hops[x], x) for x in P), default=B)
    U = set()
    limit = (k ** 2) * (2 ** (l * t))

    while len(U) < limit and not D.is_empty():
        Bi, Si = D.pull()
        if not Si:
            break
        B_i_prime, Ui = _bmssp(adj, l - 1, Bi, set(Si), db, hops, pred, k, t)
        U |= Ui

        K = []
        insert = D.insert
        for u in Ui:
            du, hu = db[u], hops[u] + 1
            for v, w in adj[u]:
                nd = du + w
                dv = db[v]
                if nd < dv:
                    db[v] = nd; hops[v] = hu; pred[v] = u
                elif nd == dv:
                    p = pred[v]
                    if (hu, u) < (hops[v], v if p < 0 else p):
                        hops[v] = hu; pred[v] = u
                else:
                    continue
                key_v = (db[v], hops[v], v)
                if Bi <= key_v < B:
                    insert(v, key_v)
                elif B_i_prime <= key_v < Bi:
                    K.append((v, key_v))
        for x in Si:
            key_x = (db[x], hops[x], x)
            if B_i_prime <= key_x < Bi:
                K.append((x, key_x))
        D.batch_prepend(K)
        B_prime = min(B_i_prime, B)

    U |= {x for x in W if (db[x], hops[x], x) < B_prime}
    return B_prime, U


def sssp_duan_et_al_fast(graph, source, return_pred=False):
    """Retorna as distâncias a partir de source. Com return_pred=True, retorna
    (dist, pred), em que pred[v] é o predecessor de v num caminho mínimo; use
    shortest_path(pred, source, v) para reconstruir o caminho."""
    # Renumeração: vértices com arestas de saída, destinos e a origem
    names = list(graph.adj.keys())
    idx = {v: i for i, v in enumerate(names)}
    for edges in graph.adj.values():
        for v, _ in edges:
            if v not in idx:
                idx[v] = len(names)
                names.append(v)
    if source not in idx:
        idx[source] = len(names)
        names.append(source)
    N = len(names)
    adj = [[] for _ in range(N)]
    for u, edges in graph.adj.items():
        adj[idx[u]] = [(idx[v], w) for v, w in edges]

    db = [INF] * N
    hops = [0] * N
    pred = [-1] * N
    s = idx[source]
    db[s] = 0

    n = len(graph.adj)
    k = max(2, int(math.log2(n) ** (1 / 3))) if n > 1 else 2
    t = max(2, int(math.log2(n) ** (2 / 3))) if n > 1 else 2
    l = int(math.log2(n) / t) + 1 if n > 1 else 1
    _bmssp(adj, l, TOP, {s}, db, hops, pred, k, t)

    dist = {names[i]: d for i, d in enumerate(db) if d < INF}
    if return_pred:
        return dist, {names[i]: names[p] for i, p in enumerate(pred) if p >= 0}
    return dist
