"""Faithful BMSSP components, Algorithm 1 and Algorithm 2 (Duan et al.).

Work in progress: uses TotalOrder from legacy module, pending a separate
full reverse-path tie-breaking implementation. NOT a complete BMSSP.
"""
import heapq
from collections import defaultdict


def base_case_faithful(graph, B, S, db, k, order):
    """Algorithm 2: bounded mini-Dijkstra; exclusive return boundary."""
    if len(S) != 1:
        raise ValueError("BaseCase requires a singleton frontier")
    x = next(iter(S))
    reached = set()
    heap = [(order.key(x, db), x)]
    while heap and len(reached) < k + 1:
        key_u, u = heapq.heappop(heap)
        if u in reached or key_u != order.key(u, db):
            continue
        if key_u >= B:
            break
        reached.add(u)
        for v, w in graph.adj[u]:
            if w < 0:
                raise ValueError("BMSSP requires nonnegative weights")
            candidate = db[u] + w
            previous = db[v]
            if candidate <= previous:
                _, key_v = order.relax(u, v, w, db)
                if key_v < B and v not in reached:
                    heapq.heappush(heap, (key_v, v))
    if len(reached) <= k:
        return B, reached
    boundary = max(order.key(v, db) for v in reached)
    return boundary, {v for v in reached if order.key(v, db) < boundary}


def find_pivots_faithful(graph, B, S, db, k, order):
    """Algorithm 1: bounded k-step relaxations and predecessor forest.

    The equality check is evaluated BEFORE relaxing. Ties must be resolved
    consistently through order.relax for predecessor forest maintenance.
    """
    if not S:
        return set(), set()
    W = set(S)
    previous_layer = set(S)
    for _ in range(k):
        layer = set()
        for u in previous_layer:
            for v, weight in graph.adj[u]:
                if weight < 0:
                    raise ValueError("BMSSP requires nonnegative weights")
                candidate = db[u] + weight
                old = db[v]
                if candidate <= old:
                    _, key_v = order.relax(u, v, weight, db)
                    if key_v < B:
                        layer.add(v)
        W.update(layer)
        if len(W) > k * len(S):
            return set(S), W
        previous_layer = layer

    # A forest from current predecessor labels. Detect invalid cycles rather
    # than hiding them (requires a consistent path total order).
    parent = {v: order.pred[v] for v in W
              if v in order.pred and order.pred[v] in W and order.pred[v] != v}
    children = defaultdict(list)
    for v, p in parent.items():
        children[p].append(v)

    pivots = set()
    for root in S:
        if root in parent:
            continue
        seen = set()
        stack = [root]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            stack.extend(children[u])
        if len(seen) >= k:
            pivots.add(root)
    return pivots, W
