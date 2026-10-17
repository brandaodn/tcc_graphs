"""Instrumentação de custo da variante experimental sem modificar produção.

Uso: python -m tests.profile_quota_pending
Mede chamadas de TotalOrder.relax, pull, insert e o tempo de execução.
Relaxaçōes repetidas incluem as realizadas por find_pivots e base_case.
Não prova limites assintóticos.
"""
import json
import random
import time
from collections import Counter
from unittest.mock import patch

from graphs.graphs import Graph, dijkstra
from graphs.batch_pq import TotalOrder, BatchPQ
from graphs.bmssp_frontier_experimental import sssp_frontier_experimental


def make_graph(n, probability, mode):
    rng = random.Random(20261017 + n * 17 + int(probability * 1000)
                        + (mode == "positive"))
    graph = Graph()
    for vertex in range(n):
        graph.adj[vertex] = []
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < probability:
                weight = 0 if mode == "zero" else rng.randint(1, 20)
                graph.add_edge(u, v, weight)
    return graph, rng.randrange(n)


def main():
    original_relax = TotalOrder.relax
    original_pull = BatchPQ.pull
    original_insert = BatchPQ.insert
    records = []

    for n in (16, 32, 64, 96):
        for probability in (0.03, 0.12, 0.4):
            for mode in ("zero", "positive"):
                graph, source = make_graph(n, probability, mode)
                counters = Counter()

                def relax(obj, *args):
                    counters["relax"] += 1
                    return original_relax(obj, *args)

                def pull(obj, *args):
                    counters["pull"] += 1
                    return original_pull(obj, *args)

                def insert(obj, *args):
                    counters["insert"] += 1
                    return original_insert(obj, *args)

                with patch.object(TotalOrder, "relax", relax), \
                     patch.object(BatchPQ, "pull", pull), \
                     patch.object(BatchPQ, "insert", insert):
                    begin = time.perf_counter()
                    observed = sssp_frontier_experimental(
                        graph, source, quota_pending_probe=True,
                        max_iterations=500)
                    elapsed = time.perf_counter() - begin

                expected = dijkstra(graph, source)
                edges = sum(map(len, graph.adj.values()))
                row = {
                    "n": n, "density": probability, "weights": mode,
                    "edges": edges, "seconds": elapsed,
                    "correct": observed == expected, **counters
                }
                records.append(row)
                print(row)
    with open("quota_cost_results.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


if __name__ == "__main__":
    main()
