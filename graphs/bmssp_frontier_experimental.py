"""Variante EXPERIMENTAL de BMSSP: condição de igualdade e detecção de ciclos.

Não utilizar em benchmarks como implementação validada do algoritmo de
Duan et al. Não usa Dijkstra como fallback. O limite de repetição serve
somente para produzir contraexemplos e evitar execuções indefinidas.

Uso:
    from graphs.bmssp_frontier_experimental import sssp_frontier_experimental
"""
from collections import defaultdict
import math

from graphs.batch_pq import INF, TotalOrder, BatchPQ
from graphs.duan_et_al import base_case, find_pivots


class RepeatedFrontierError(RuntimeError):
    """A recursão revisitou uma fronteira sem mudança no estado observado."""


def bmssp_frontier(graph, level, bound, sources, dist, k, t, order,
                   *, diagnostics, max_iterations=10000):
    if level == 0:
        return base_case(graph, next(iter(sources)), bound, dist, k, order)

    pivots, visited = find_pivots(graph, sources, bound, dist, k, order)
    queue = BatchPQ(M=2 ** ((level - 1) * t), B=bound)
    for x in pivots:
        queue.insert(x, order.key(x, dist))

    boundary = min((order.key(x, dist) for x in pivots), default=bound)
    complete = set()
    seen_states = set()
    limit = k ** 2 * 2 ** (level * t)

    while len(complete) < limit and not queue.is_empty():
        # Representação do estado efetivo: vértices, chaves e distâncias.
        state = (
            level, bound, tuple(sorted(map(repr, complete))),
            tuple(sorted((repr(x), repr(key))
                         for x, key in queue._key_val.items())),
            tuple(sorted((repr(x), repr(value))
                         for x, value in dist.items())),
        )
        if state in seen_states:
            diagnostics.append({
                "reason": "repeated_state", "level": level,
                "boundary": repr(boundary),
                "queue": repr(queue._key_val),
                "complete": repr(complete),
            })
            raise RepeatedFrontierError(
                f"Estado repetido em BMSSP(level={level}), "
                f"boundary={boundary}, queue={queue._key_val}"
            )
        seen_states.add(state)
        if len(seen_states) > max_iterations:
            raise RepeatedFrontierError(
                f"Orçamento de iterações excedido no nível {level}"
            )
        next_bound, batch = queue.pull()
        if not batch:
            if not queue.is_empty():
                raise RepeatedFrontierError(
                    f"Pull vazio com fila não vazia no nível {level}"
                )
            break
        child_boundary, child_complete = bmssp_frontier(
            graph, level - 1, next_bound, set(batch), dist, k, t,
            order, diagnostics=diagnostics, max_iterations=max_iterations
        )
        complete.update(child_complete)
        prepend = []
        for u in child_complete:
            for v, weight in graph.adj[u]:
                previous = dist[v]
                candidate = dist[u] + weight
                # A condição do artigo inclui igualdade; relax somente
                # atualiza a chave, não governa elegibilidade da aresta.
                _, key_v = order.relax(u, v, weight, dist)
                if candidate <= previous:
                    if next_bound <= key_v < bound:
                        queue.insert(v, key_v)
                    elif child_boundary <= key_v < next_bound:
                        prepend.append((v, key_v))
        prepend.extend((x, order.key(x, dist)) for x in batch
                       if child_boundary <= order.key(x, dist) < next_bound)
        queue.batch_prepend(prepend)
        boundary = min(child_boundary, bound)

    complete.update(x for x in visited if order.key(x, dist) < boundary)
    return boundary, complete


def sssp_frontier_experimental(graph, source, *, max_iterations=10000):
    dist = defaultdict(lambda: INF)
    dist[source] = 0
    order = TotalOrder()
    order.rank(source)
    vertices = {source} | set(graph.adj)
    vertices.update(v for edges in graph.adj.values() for v, _ in edges)
    n = len(vertices)
    k = max(2, int(math.log2(n) ** (1 / 3))) if n > 1 else 2
    t = max(2, int(math.log2(n) ** (2 / 3))) if n > 1 else 2
    level = int(math.log2(n) / t) + 1 if n > 1 else 1
    diagnostics = []
    bmssp_frontier(graph, level, order.TOP, {source}, dist, k, t,
                   order, diagnostics=diagnostics,
                   max_iterations=max_iterations)
    return {v: dist[v] for v in vertices}
