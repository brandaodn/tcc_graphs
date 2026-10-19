from collections import namedtuple
from graphs.graphs import Graph

CHAIN_EDGE_WEIGHT = 0.0
CYCLE_EDGE_WEIGHT = 0.0

# Vértice auxiliar criado por constant_degree: a i-ésima cópia do vértice
# original v. A cópia 0 é o próprio v, que representa o vértice no ciclo.
AuxVertex = namedtuple("AuxVertex", "v i")


def original_vertex(x):
    """Vértice do grafo original ao qual x pertence em constant_degree (o
    próprio x se ele não for auxiliar)."""
    if isinstance(x, AuxVertex):
        return x.v
    return x


def is_original_vertex(x):
    """True se x não é um vértice auxiliar criado por bounded_out_degree
    ("u#1", "u#2", ...) ou por constant_degree (AuxVertex)."""
    return not (isinstance(x, AuxVertex) or (isinstance(x, str) and "#" in x))


def bounded_out_degree(graph: Graph, max_degree: int = 2) -> Graph:
    
    assert max_degree >= 2, "max_degree precisa ser >= 2"

    new_g = Graph()
    slots_por_no = max_degree - 1  

    for u, edges in graph.adj.items():
        if len(edges) <= max_degree:
            for v, w in edges:
                new_g.add_edge(u, v, w)
            continue

        
        chunks = []
        i, n = 0, len(edges)
        while i < n:
            restante = n - i
            if restante <= max_degree:
                chunks.append(edges[i:])
                i = n
            else:
                chunks.append(edges[i:i + slots_por_no])
                i += slots_por_no

        node_names = [u] + [f"{u}#{k}" for k in range(1, len(chunks))]

        for idx, (nome, chunk) in enumerate(zip(node_names, chunks)):
            for v, w in chunk:
                new_g.add_edge(nome, v, w)
            if idx < len(node_names) - 1:
                new_g.add_edge(nome, node_names[idx + 1], CHAIN_EDGE_WEIGHT)  

    # preserva vértices-folha (sem arestas de saída) que existiam no original
    for u in graph.adj:
        if u not in new_g.adj:
            new_g.adj[u] = []

    return new_g


def constant_degree(graph: Graph) -> Graph:
    """Transformação para grau de entrada e de saída constantes, como pressuposto
    por Duan et al.: cada vértice v é substituído por um ciclo de arestas de
    peso zero com um vértice x_{v,w} para cada vizinho w de v (de entrada ou de
    saída), e cada aresta (u, v) vira a aresta x_{u,v} -> x_{v,u}, com o mesmo
    peso. Todo vértice resultante tem grau de entrada e de saída <= 2, e o grafo
    tem O(m) vértices e arestas.

    O vértice x_{v,w} de menor índice no ciclo é o próprio v, de modo que
    dist[v] no grafo transformado é a distância de v no original. Os demais
    são AuxVertex(v, i). Arestas paralelas ficam só com o menor peso."""
    weight = {}
    neighbors = {u: {} for u in graph.adj}
    for u, edges in graph.adj.items():
        for v, w in edges:
            if u == v:
                continue  # laço não altera distâncias com pesos >= 0
            if (u, v) not in weight or w < weight[(u, v)]:
                weight[(u, v)] = w
            neighbors.setdefault(v, {})
            # dict preserva a ordem de inserção: ciclo determinístico
            neighbors[u].setdefault(v, None)
            neighbors[v].setdefault(u, None)

    node = {}  # (v, w) -> vértice x_{v,w}
    new_g = Graph()
    for v, nbrs in neighbors.items():
        cycle = [v if i == 0 else AuxVertex(v, i) for i in range(max(1, len(nbrs)))]
        for x in cycle:
            new_g.adj[x]  # garante a chave mesmo sem arestas de saída
        for i, w in enumerate(nbrs):
            node[(v, w)] = cycle[i]
        if len(cycle) > 1:
            for i, x in enumerate(cycle):
                new_g.add_edge(x, cycle[(i + 1) % len(cycle)], CYCLE_EDGE_WEIGHT)

    for (u, v), w in weight.items():
        new_g.add_edge(node[(u, v)], node[(v, u)], w)

    return new_g

