"""Experimental BMSSP plus frontier completion (NOT pure Duan BMSSP).

This independent variant makes the extra heap-based step explicit. It must
not be used to claim the asymptotic guarantees of the original algorithm.
"""
import heapq
from itertools import count
from math import inf

from graphs.duan_et_al import sssp_duan_et_al
from graphs.duan_et_al_iter import sssp_duan_et_al_iter
from graphs.duan_et_al_opt import sssp_duan_et_al_opt


def finish_frontier(graph, source, tentative):
    """Complete tentative source-path upper bounds for nonnegative edge weights.

    Finite tentative values must represent valid source-path lengths.
    The heap phase is conventional label-correcting/Dijkstra-style work.
    """
    vertices = {source} | set(graph.adj)
    for u, adjacent in graph.adj.items():
        vertices.update(v for v, _ in adjacent)
        for v, weight in adjacent:
            if weight < 0:
                raise ValueError("finish_frontier requires nonnegative weights")
    dist = {v: tentative.get(v, inf) for v in vertices}
    dist[source] = 0
    counter = count()
    heap = [(d, next(counter), v) for v, d in dist.items() if d < inf]
    heapq.heapify(heap)
    while heap:
        du, _, u = heapq.heappop(heap)
        if du != dist[u]:
            continue
        for v, weight in graph.adj[u]:
            nd = du + weight
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, next(counter), v))
    return dist


def sssp_duan_et_al_completed(graph, source):
    return finish_frontier(graph, source, sssp_duan_et_al(graph, source))


def sssp_duan_et_al_iter_completed(graph, source):
    return finish_frontier(graph, source, sssp_duan_et_al_iter(graph, source))


def sssp_duan_et_al_opt_completed(graph, source):
    return finish_frontier(graph, source, sssp_duan_et_al_opt(graph, source))
