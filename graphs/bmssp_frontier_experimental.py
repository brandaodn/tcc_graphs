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
                   *, diagnostics, max_iterations=10000, boundary_probe=False,
                   pending_probe=False):
    if level == 0:
        child_bound, finished = base_case(graph, next(iter(sources)), bound, dist, k, order)
        if boundary_probe:
            # EXPERIMENTAL: incluir o vertice exatamente no limite no
            # resultado operacional; NAO equivale ao conjunto finalizado
            # definido pelo artigo.
            finished = set(finished) | {
                v for v in dist if order.key(v, dist) == child_bound
            }
        if pending_probe:
            pending = {v for v in dist if order.key(v, dist) == child_bound}
            return child_bound, finished, pending
        return child_bound, finished

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
        before_complete = set(complete)
        before_dist = dict(dist)
        extracted_keys = {v: order.key(v, dist) for v in batch}
        child_return = bmssp_frontier(
            graph, level - 1, next_bound, set(batch), dist, k, t,
            order, diagnostics=diagnostics, max_iterations=max_iterations,
            boundary_probe=boundary_probe, pending_probe=pending_probe
        )
        if pending_probe:
            child_boundary, child_complete, child_pending = child_return
        else:
            child_boundary, child_complete = child_return
            child_pending = set()
        complete.update(child_complete)
        prepend = []
        for u in child_complete | child_pending:
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
        # Diagnóstico das duas origens da reinserção: K (arestas) e Si.
        from_k = list(prepend)
        from_si = [(x, order.key(x, dist)) for x in batch
                   if child_boundary <= order.key(x, dist) < next_bound]
        from_k_vertices = {v for v, _ in from_k}
        from_si_vertices = {v for v, _ in from_si}
        overlap = from_k_vertices & from_si_vertices
        # Uma duplicata entre K e Si não representa duas tarefas distintas.
        # BatchPQ já faz deduplicação; aqui registramos a proveniência
        # explicitamente antes de aplicar a mesma operação.
        before = dict(queue._key_val)
        # Um elemento de Si ausente de Ui não foi declarado concluído
        # pelo filho. Registre este possível trabalho pendente.
        uncompleted = [(x, order.key(x, dist)) for x in batch
                       if x not in child_complete]
        if uncompleted:
            diagnostics.append({
                "reason": "batch_not_in_child_complete",
                "level": level,
                "sources": sorted(map(repr, sources)),
                "batch": [(repr(v), repr(order.key(v, dist))) for v in batch],
                "missing_from_Ui": [(repr(v), repr(key)) for v, key in uncompleted],
                "child_boundary": repr(child_boundary),
                "next_bound": repr(next_bound),
                "from_K": [(repr(v), repr(key)) for v, key in from_k],
                "from_Si": [(repr(v), repr(key)) for v, key in from_si],
            })
        prepend.extend(from_si)
        if boundary_probe or pending_probe:
            no_progress = (set(child_complete).issubset(before_complete)
                           and dict(dist) == before_dist)
            if no_progress:
                prepend = [(v, key) for v, key in prepend
                           if extracted_keys.get(v) != key]
        queue.batch_prepend(prepend)
        after = dict(queue._key_val)
        diagnostics.append({
            "reason": "post_recursive_prepend",
            "level": level,
            "batch": sorted(map(repr, batch)),
            "child_complete": sorted(map(repr, child_complete)),
            "next_bound": repr(next_bound),
            "child_boundary": repr(child_boundary),
            "from_K": [(repr(v), repr(key)) for v, key in from_k],
            "from_Si": [(repr(v), repr(key)) for v, key in from_si],
            "overlap": sorted(map(repr, overlap)),
            "queue_before": [(repr(v), repr(key)) for v, key in before.items()],
            "queue_after": [(repr(v), repr(key)) for v, key in after.items()],
            "changed": before != after,
        })
        boundary = min(child_boundary, bound)

    complete.update(x for x in visited if order.key(x, dist) < boundary)
    if pending_probe:
        return boundary, complete, {v for v in dist if order.key(v, dist) == boundary}
    return boundary, complete


def sssp_frontier_experimental(graph, source, *, max_iterations=10000, diagnostics=None, boundary_probe=False,
                               pending_probe=False):
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
    if diagnostics is None:
        diagnostics = []
    bmssp_frontier(graph, level, order.TOP, {source}, dist, k, t,
                   order, diagnostics=diagnostics,
                   max_iterations=max_iterations,
                   boundary_probe=boundary_probe,
                   pending_probe=pending_probe)
    return {v: dist[v] for v in vertices}
