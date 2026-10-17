"""Diagnóstico da primeira repetição de fronteira no BMSSP experimental.

Executar na raiz:
  python3 tests/trace_first_reinsertion.py --case 21

Inspeciona eventos de insert/pull/batch_prepend por monkeypatch temporário,
restaurado ao final. Captura histórico limitado e compara estado anterior e
posterior. Apenas diagnóstico; não modifica os algoritmos.
"""
import argparse
import json
import random
from collections import deque
from unittest.mock import patch

from graphs.graphs import Graph
from graphs.batch_pq import BatchPQ
from graphs.bmssp_frontier_experimental import (
    RepeatedFrontierError, sssp_frontier_experimental,
)


def build_case(index):
    rng = random.Random(20261017)
    for _ in range(index + 1):
        n = rng.randint(2, 16)
        probability = rng.choice([0.08, 0.2, 0.5])
        edges = [(u, v, rng.randint(0, 9))
                 for u in range(n) for v in range(n)
                 if u != v and rng.random() < probability]
        source = rng.randrange(n)
    g = Graph()
    for v in range(n):
        g.adj[v] = []
    for u, v, weight in edges:
        g.add_edge(u, v, weight)
    return g, source


def inspect(index, output, history_size):
    graph, source = build_case(index)
    recent = deque(maxlen=history_size)
    counter = [0]

    def describe(q):
        return sorted(
            [(repr(v), repr(k)) for v, k in q._key_val.items()]
        )

    originals = {
        "insert": BatchPQ.insert,
        "pull": BatchPQ.pull,
        "batch_prepend": BatchPQ.batch_prepend,
    }

    def record(operation, q, before, after, arguments, result=None):
        counter[0] += 1
        recent.append({
            "seq": counter[0], "queue_id": id(q),
            "operation": operation, "arguments": repr(arguments),
            "before": before, "after": after,
            "changed": before != after, "result": repr(result),
        })

    def insert(q, vertex, key):
        before = describe(q)
        result = originals["insert"](q, vertex, key)
        record("insert", q, before, describe(q), (vertex, key), result)
        return result

    def pull(q):
        before = describe(q)
        result = originals["pull"](q)
        record("pull", q, before, describe(q), (), result)
        return result

    def batch_prepend(q, pairs):
        before = describe(q)
        # capture iterator input in case an implementation supplies one
        pairs = list(pairs)
        result = originals["batch_prepend"](q, pairs)
        record("batch_prepend", q, before, describe(q), pairs, result)
        return result

    status = "completed"
    recursive_events = []
    with patch.object(BatchPQ, "insert", insert), \
         patch.object(BatchPQ, "pull", pull), \
         patch.object(BatchPQ, "batch_prepend", batch_prepend):
        try:
            sssp_frontier_experimental(graph, source, max_iterations=1000, diagnostics=recursive_events)
        except RepeatedFrontierError as exc:
            status = f"RepeatedFrontierError: {exc}"

    report = {
        "case": index, "source": source,
        "n": len(graph.adj), "status": status,
        "operation_count": counter[0],
        "last_operations": list(recent),
        "last_recursive_events": recursive_events[-30:],
        "recursion_K_Si_overlaps": sum(bool(e.get("overlap")) for e in recursive_events),
    }
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(status)
    print(f"Operações monitoradas: {counter[0]}")
    print(f"Arquivo: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, default=21)
    parser.add_argument("--output", default="trace_first_reinsertion.json")
    parser.add_argument("--history-size", type=int, default=80)
    args = parser.parse_args()
    inspect(args.case, args.output, args.history_size)
