import math
from collections import defaultdict
from graphs.batch_pq import INF, TotalOrder, BatchPQ
from graphs.duan_et_al import base_case, find_pivots


class _Frame:
    __slots__ = ("l", "B", "S", "W", "D", "U", "B_prime", "limit", "Bi", "Si")


def _open_frame(graph, l, B, S, db, k, t, order):
    f = _Frame()
    f.l, f.B, f.S = l, B, S
    if l == 0:
        return f                      # Caso base é resolvido no laço principal
    P, f.W = find_pivots(graph, S, B, db, k, order)
    f.D = BatchPQ(M=2 ** ((l - 1) * t), B=B)
    for x in P:
        f.D.insert(x, order.key(x, db))
    f.B_prime = min((order.key(x, db) for x in P), default=B)
    f.U = set()
    f.limit = (k ** 2) * (2 ** (l * t))
    f.Bi = f.Si = None
    return f


def _absorb(f, ret, graph, db, order):
    """Pós-chamada: equivale ao que vinha após a chamada recursiva."""
    B_i_prime, Ui = ret
    Bi, Si, B, D = f.Bi, f.Si, f.B, f.D
    f.U |= Ui
    K = []
    for u in Ui:
        for v, w in graph.adj[u]:
            accepted, key_v = order.relax(u, v, w, db)
            if accepted:
                if Bi <= key_v < B:
                    D.insert(v, key_v)
                elif B_i_prime <= key_v < Bi:
                    K.append((v, key_v))
    K += [(x, order.key(x, db)) for x in Si
          if B_i_prime <= order.key(x, db) < Bi]
    D.batch_prepend(K)
    f.B_prime = min(B_i_prime, B)


def BMSSP_iter(graph, l, B_key, S, db, k, t, order: TotalOrder):
    stack = [_open_frame(graph, l, B_key, S, db, k, t, order)]
    ret = None
    while True:
        f = stack[-1]

        # Caso base (l == 0): resolve e "retorna"
        if f.l == 0:
            ret = base_case(graph, next(iter(f.S)), f.B, db, k, order)
            stack.pop()
            if not stack:
                return ret
            continue

        # Um filho acabou de retornar: processa o pós-chamada
        if ret is not None:
            _absorb(f, ret, graph, db, order)
            ret = None

        # Próxima iteração do while
        if len(f.U) < f.limit and not f.D.is_empty():
            Bi, Si = f.D.pull()
            if Si:
                f.Bi, f.Si = Bi, Si
                stack.append(_open_frame(graph, f.l - 1, Bi, set(Si),
                                         db, k, t, order))
                continue              # "Chamada recursiva"

        # Fim do while: finaliza o frame e "retorna"
        f.U |= {x for x in f.W if order.key(x, db) < f.B_prime}
        ret = (f.B_prime, f.U)
        stack.pop()
        if not stack:
            return ret


def sssp_duan_et_al_iter(graph, source, return_pred=False):
    """Retorna as distâncias a partir de source. Com return_pred=True, retorna
    (dist, pred), em que pred[v] é o predecessor de v num caminho mínimo; use
    shortest_path(pred, source, v) para reconstruir o caminho."""
    db = defaultdict(lambda: INF)
    db[source] = 0
    order = TotalOrder()
    order.rank(source)
    n = len(graph.adj)
    k = max(2, int(math.log2(n) ** (1 / 3))) if n > 1 else 2
    t = max(2, int(math.log2(n) ** (2 / 3))) if n > 1 else 2
    l = int(math.log2(n) / t) + 1 if n > 1 else 1
    BMSSP_iter(graph, l, order.TOP, {source}, db, k, t, order)
    if return_pred:
        return dict(db), dict(order.pred)
    return dict(db)
