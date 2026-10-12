import heapq
import random
from collections import defaultdict, deque
import os
import json

class Graph:
    def __init__(self):
        self.adj = defaultdict(list)

    def add_edge(self, u, v, w):
        self.adj[u].append((v, w))

    def save(self, path):
            vertices = sorted(self.adj.keys(), key=str)
            edges = [
                [u, v, w]
                for u in self.adj
                for v, w in self.adj[u]
            ]
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w") as f:
                json.dump({"vertices": vertices, "edges": edges}, f)

    @classmethod
    def load(cls, path):
        with open(path) as f:
            data = json.load(f)
        g = cls()
        for v in data["vertices"]:
            g.adj[v]  # garante a chave mesmo sem arestas (defaultdict)
        for u, v, w in data["edges"]:
            g.add_edge(u, v, w)
        return g

def save_graph(graph, path):
    """Atalho funcional para graph.save(path), no estilo das outras
    funções deste módulo (dijkstra, generate_random_graph, etc.)."""
    graph.save(path)

def load_graph(path):
    """Atalho funcional para Graph.load(path)."""
    return Graph.load(path)


def graph_cache_path(dir_path, num_v, k, i):
    """Nome de arquivo padronizado para um grafo salvo, consistente com o
    identificador 'graph' já usado em random_test.py (ex: n1000k3.00i2)."""
    return os.path.join(dir_path, f"n{num_v}k{k:.2f}i{i}.json")

def dijkstra(graph, source):
    INF = float('inf')

    # pega todos os vértices (origem + destinos)
    vertices = set(graph.adj.keys())
    for u in graph.adj:
        for v, _ in graph.adj[u]:
            vertices.add(v)

    dist = {v: INF for v in vertices}
    dist[source] = 0.0

    count = 0
    pq = [(0, count, source)]
    

    while pq:
        dist_u, _, u = heapq.heappop(pq)

        if dist_u > dist[u]:
            continue

        for v, w in graph.adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                count += 1
                heapq.heappush(pq, (dist[v], count, v))

    return dist

def bellman_ford(graph, source):
    INF = float('inf')

    # todos os vértices (inclui folhas)
    vertices = set(graph.adj.keys())
    for u in graph.adj:
        for v, _ in graph.adj[u]:
            vertices.add(v)

    dist = {v: INF for v in vertices}
    dist[source] = 0

    n = len(vertices)

    for _ in range(n - 1):
        changed = False

        for u in graph.adj:
            for v, w in graph.adj[u]:
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    changed = True

        if not changed:
            break

    return dist

def generate_random_graph(num_vertices, edge_probability):
    g = Graph()
    for u in range(num_vertices):
        for v in range(num_vertices):
            if u != v and random.random() < edge_probability:
                w = random.randint(1, 10)
                g.add_edge(u, v, w)
    return g

def is_fully_reachable(graph, source, num_vertices):
    """Retorna True se todos os vértices são alcançáveis a partir de source."""
    visited = {source}
    queue = deque([source])

    while queue:
        u = queue.popleft()
        for v, _ in graph.adj[u]:
            if v not in visited:
                visited.add(v)
                queue.append(v)

    return len(visited) == num_vertices