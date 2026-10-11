from random import seed
from graphs.graphs import (
    dijkstra,
    generate_random_graph,
    is_fully_reachable,
    save_graph,
    load_graph,
    graph_cache_path,
)
from graphs.duan_et_al import sssp_duan_et_al
from graphs.duan_et_al_iter import sssp_duan_et_al_iter
from time import process_time
import sys
from graphs.degree_reduction import bounded_out_degree
import csv
from datetime import datetime
import os
import argparse


parser = argparse.ArgumentParser(
    description="Executa testes comparativos em grafos aleatórios.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument(
    "--track",
    dest="salvar",
    action="store_const",
    const="--track",
    help="Salva resultados na pasta pública 'data/' para serem subidos ao GitHub."
)
group.add_argument(
    "--untrack",
    dest="salvar",
    action="store_const",
    const="--untrack",
    help="Salva resultados na pasta privada 'data/untracked_results/'."
)
parser.add_argument(
    "--mode",
    choices=["generate", "load"],
    default="generate",
    help="Modo de execução: 'generate' para novos grafos em memória, 'load' para usar grafos salvos."
)
parser.add_argument(
    "--path",
    type=str,
    default="data/graphs",
    help="Caminho do diretório de grafos salvos (usado no modo 'load')."
)
parser.add_argument(
    "--seed",
    type=int,
    default=42,
    help="Semente (seed) para o gerador de números aleatórios (usado no modo 'generate')."
)
parser.add_argument(
    "--executions-per-graph",
    dest="executions_per_graph",
    type=int,
    default=5,
    help="Quantas vezes cada algoritmo é executado sobre o MESMO grafo, para reduzir ruído na medição de tempo."
)
parser.add_argument(
    "--transform",
    dest="transform",
    action="store_true",
    help="Aplica a transformação de redução de grau (bounded_out_degree) no grafo antes de executar os algoritmos."
)
parser.add_argument(
    "--output-dir",
    type=str,
    default=None,
    help="Diretório de destino para salvar o arquivo CSV de resultados."
)
parser.add_argument(
    "--algorithms",
    nargs="+",
    default=["dijkstra", "sssp_duan_et_al", "sssp_duan_et_al_iter", "sssp_duan_et_al_opt"],
    help="Algoritmos a executar: dijkstra, sssp_duan_et_al, sssp_duan_et_al_iter, sssp_duan_et_al_opt, sssp_duan_et_al_opt_iter."
)

args = parser.parse_args()

salvar = args.salvar

# Garantir reprodutibilidade
seed(args.seed)

# Quantidade de grafos por configuração
num_graphs = 5

num_vertices = (10000, 50000, 100000)

# Grau médio
grau_médio = (5, 3, 1, 0.8, 0.7, 0.5) 

# Mapeamento e seleção dos algoritmos
ALGO_MAP = {
    "dijkstra": dijkstra,
    "sssp_duan_et_al": sssp_duan_et_al,
    "sssp_duan_et_al_iter": sssp_duan_et_al_iter,
    "sssp_duan_et_al_opt": sssp_duan_et_al_opt,
    "sssp_duan_et_al_opt_iter": sssp_duan_et_al_opt_iter,
}
algorithms = tuple(ALGO_MAP[name] for name in args.algorithms)

executions_per_graph = args.executions_per_graph

results = []

qt_executions = (
    len(num_vertices)
    * len(grau_médio)
    * len(algorithms)
    * num_graphs
)

current_execution = 0

for num_v in num_vertices:
    for k in grau_médio:

        # conversão para probabilidade equivalente no G(n, p)
        edge_prob = k / (num_v - 1)

        # estimativa realista de número de arestas
        edge_estimate = (num_v * k)

        for i in range(num_graphs):

            if args.mode == "load":
                graph_path = graph_cache_path(args.path, num_v, k, i)
                if not os.path.exists(graph_path):
                    print(
                        f"\nErro: Grafo não encontrado em '{graph_path}'.\n"
                        f"Certifique-se de ter gerado os grafos com o script 'generate_graphs.py' "
                        f"ou rode no modo '--mode generate'."
                    )
                    sys.exit(1)
                g_raw = load_graph(graph_path)
            else:
                # args.mode == "generate"
                g_raw = generate_random_graph(num_v, edge_prob)

            if args.transform:
                g = bounded_out_degree(g_raw, 2)
            else:
                g = g_raw

            ref_dist = None
            for alg in algorithms:

                for j in range(executions_per_graph):

                    current_execution += 1
                    progress = (current_execution / qt_executions) * 100

                    print(
                        f"\rExecuted {progress:.2f}% "
                        f"| num_vertices: {num_v} "
                        f"| k(avg_degree): {k:.2f} "
                        f"| algorithm: {alg.__name__} "
                        f"| edge_estimate: {edge_estimate:.0f}      "
                        f"| graph: {i + 1}/{num_graphs} "
                        f"| repetition: {j + 1}/{executions_per_graph}      ",
                        end="",
                        flush=True
                    )

                    source = 0
                    start_time = process_time()
                    dist = alg(g, source)
                    end_time = process_time()

                    delta_time = end_time - start_time

                    num_explored = sum(1 for v in dist if dist[v] < float('inf'))
                    explored_percentage = (num_explored / num_v) * 100

                    if alg == dijkstra:
                        ref_dist = dist
                        is_correct = True
                        error_count = 0
                    else:
                        if ref_dist is None:
                            ref_dist = dijkstra(g, source)
                        error_count = sum(
                            1 for v, d in ref_dist.items()
                            if (dist.get(v, float('inf')) != d and abs(dist.get(v, float('inf')) - d) > 1e-9)
                        )
                        is_correct = (error_count == 0)

                    results.append({
                        "num_vertices": num_v,
                        "avg_degree_k": k,
                        "algorithm": alg.__name__,
                        "execution_time": delta_time,
                        "edge_estimate": edge_estimate,
                        "graph": f"n{num_v}k{k:.2f}i{i}",
                        "fully_reachable": is_fully_reachable(g, source, num_v),
                        "explored_percentage": explored_percentage,
                        "is_correct": is_correct,
                        "error_count": error_count
                    })

print("\nExecution finished.")

# Nome dessa instância do teste com a data e hora atual
name = f"results-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"

if args.output_dir:
    dir = args.output_dir if args.output_dir.endswith(('/', '\\')) else args.output_dir + '/'
else:
    dir = "data/untracked_results/" if salvar == "--untrack" else "data/"

# Criar diretório se não existir
if not os.path.exists(dir):
    os.makedirs(dir)

# Salvar os resultados em CSV
with open(f'{dir}{name}.csv', 'w', newline='') as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "num_vertices",
            "avg_degree_k",
            "algorithm",
            "execution_time",
            "edge_estimate",
            "graph",
            "fully_reachable",
            "explored_percentage",
            "is_correct",
            "error_count"
        ]
    )

    writer.writeheader()
    writer.writerows(results)