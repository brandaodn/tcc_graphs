"""Profile BMSSP experimental progress at recursive level 1.

Run from repository root:
 python -m tests.profile_level1_progress

This is diagnostic instrumentation, not an algorithm modification.
"""
import json
import random
from collections import Counter
from unittest.mock import patch
from graphs.graphs import Graph, dijkstra
from graphs.batch_pq import BatchPQ
from graphs.bmssp_frontier_experimental import sssp_frontier_experimental


def main():
    n, p = 1024, 0.12
    rng = random.Random(20261017 + n * 17 + int(p * 1000))
    graph = Graph()
    for u in range(n):
        graph.adj[u] = []
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < p:
                graph.add_edge(u, v, rng.randint(0, 20))
    source = rng.randrange(n)
    original_pull = BatchPQ.pull
    extracted = Counter()

    def pull(queue):
        result = original_pull(queue)
        if queue.M == 1:
            extracted[len(result[1])] += 1
        return result

    diagnostics = []
    with patch.object(BatchPQ, "pull", pull):
        observed = sssp_frontier_experimental(
            graph, source, quota_pending_probe=True,
            max_iterations=10000, diagnostics=diagnostics
        )
    expected = dijkstra(graph, source)
    progress = [e for e in diagnostics
                if e.get("reason") == "post_recursive_prepend"
                and e.get("level") == 1]
    print(json.dumps({
        "source": source,
        "n": n,
        "m": sum(len(edges) for edges in graph.adj.values()),
        "distance_errors": sum(observed[v] != expected[v] for v in expected),
        "level1_post_return_events": len(progress),
        "level1_pull_batch_sizes": dict(extracted),
        "level1_unchanged_queue_events": sum(not e["changed"] for e in progress),
    }, indent=2))


if __name__ == "__main__":
    main()
