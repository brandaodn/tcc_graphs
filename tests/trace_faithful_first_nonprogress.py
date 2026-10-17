"""Trace recursion stack at first BaseCase nonprogress in the local BMSSP trial.

Usage from repository root:
    python -m tests.trace_faithful_first_nonprogress

Diagnostic only. Keeps production files untouched.
"""
import random
import json
from graphs.graphs import Graph, dijkstra
import graphs.duan_et_al_faithful as algorithm

def diagnose(count=100):
    stack, events, results = [], [], []
    base = algorithm.base_case_faithful
    bmssp = algorithm.bmssp
    def traced_base(g, B, S, db, k, order):
        vertex = next(iter(S))
        initial_key = order.key(vertex, db)
        boundary, completed = base(g, B, S, db, k, order)
        if vertex not in completed and boundary <= order.key(vertex, db):
            events.append({
                "seed": repr(vertex), "initial_key": repr(initial_key),
                "result_key": repr(order.key(vertex, db)),
                "bound": repr(B), "returned_bound": repr(boundary),
                "completed": sorted(map(repr, completed)),
                "call_stack": [dict(frame) for frame in stack]
            })
        return boundary, completed
    def traced_bmssp(g, level, B, S, db, k, t, order, stats):
        stack.append({"level": level, "bound": repr(B),
                      "sources": sorted((repr(v), repr(order.key(v,db))) for v in S)})
        try:
            return bmssp(g, level, B, S, db, k, t, order, stats)
        finally:
            stack.pop()
    algorithm.base_case_faithful = traced_base
    algorithm.bmssp = traced_bmssp
    try:
        for idx in range(count):
            rng = random.Random(20261017 + idx)
            n = rng.choice((8, 12, 16, 24, 32))
            probability = rng.choice((.04,.1,.2,.4))
            graph = Graph()
            for vertex in range(n):
                graph.adj[vertex] = []
            for u in range(n):
                for v in range(n):
                    if u != v and rng.random() < probability:
                        graph.add_edge(u,v,rng.randint(0,9))
            source = rng.randrange(n)
            events.clear()
            try:
                found, _ = algorithm.sssp_faithful_trial(graph, source)
                reference = dijkstra(graph, source)
                status = "correct" if all(found[v] == reference.get(v,float("inf")) for v in range(n)) else "wrong"
            except Exception as exc:
                status = type(exc).__name__
            results.append({"case": idx, "n": n, "p": probability, "source": source,
                            "status": status, "first_nonprogress": events[0] if events else None})
    finally:
        algorithm.base_case_faithful = base
        algorithm.bmssp = bmssp
    return results

if __name__ == "__main__":
    print(json.dumps(diagnose(),indent=2))
