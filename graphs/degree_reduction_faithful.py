"""Directed degree-two reduction preparing a faithful BMSSP.

For each original arc u->v create distinct outgoing/incoming ports. Each
vertex's incident ports form a directed zero-weight cycle, preserving paths.
"""
from dataclasses import dataclass
import math
from graphs.graphs import Graph

@dataclass
class DegreeReducedGraph:
    graph: Graph
    representative: dict
    ports: dict
    original_vertices: tuple
    original_edges: int

    def project_distances(self, distances):
        return {v: distances.get(self.representative[v], math.inf)
                for v in self.original_vertices}

def reduce_to_degree_two(graph, vertices=None):
    """Build a directed graph of max in/out degree 2 in O(V+E)."""
    all_vertices = dict.fromkeys(vertices or ())
    arcs = []
    for u, edges in list(graph.adj.items()):
        all_vertices[u] = None
        for v, w in edges:
            if not isinstance(w, (int, float)) or not math.isfinite(w) or w < 0:
                raise ValueError("degree reduction requires finite nonnegative weights")
            all_vertices[v] = None
            arcs.append((u, v, w))
    ports = {v: [] for v in all_vertices}
    outgoing, incoming = [], []
    for i, (u, v, _) in enumerate(arcs):
        out_port, in_port = ("edge", i, "out"), ("edge", i, "in")
        ports[u].append(out_port)
        ports[v].append(in_port)
        outgoing.append(out_port)
        incoming.append(in_port)
    reduced = Graph()
    representative = {}
    for i, (v, ring) in enumerate(ports.items()):
        if not ring:
            ring.append(("isolate", i))
        representative[v] = ring[0]
        for node in ring:
            reduced.adj[node] = []
        if len(ring) > 1:
            for j, node in enumerate(ring):
                reduced.add_edge(node, ring[(j+1) % len(ring)], 0)
    for i, (_, _, w) in enumerate(arcs):
        reduced.add_edge(outgoing[i], incoming[i], w)
    return DegreeReducedGraph(reduced, representative, ports,
                              tuple(all_vertices), len(arcs))
