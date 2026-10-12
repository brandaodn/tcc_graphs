from time import process_time
from datetime import datetime
from graphs.graphs import Graph, dijkstra, is_fully_reachable
from graphs.duan_et_al import sssp_duan_et_al
from graphs.duan_et_al_iter import sssp_duan_et_al_iter
from graphs.duan_et_al_opt import sssp_duan_et_al_opt
from graphs.degree_reduction import bounded_out_degree
import gzip
import shutil
import csv
import os
import glob
import argparse


def load_graph(gr_file: str) -> tuple[Graph, int, int]:

    with open(gr_file, 'r') as f:
        data = f.read().splitlines()

    graph = Graph()
    n = m = 0

    for line in data:
        if line.startswith('a'):
            _, u, v, w = line.split()
            graph.add_edge(int(u), int(v), int(w))
        elif line.startswith('p'):
            _, _, n, m = line.split()

    return graph, int(n), int(m)


def process_file(arquivo_gz: str, r: int, algorithms: tuple, transformar: bool) -> list[dict]:
    """Descompacta, carrega e roda os algoritmos sobre um único arquivo .gz,
    retornando a lista de resultados (um dict por execução)."""

    file_results = []
    arquivo_gr = arquivo_gz.replace('.gz', '')

    # Descompacta o arquivo
    with gzip.open(arquivo_gz, 'rb') as f_in:
        with open(arquivo_gr, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    graph, num_vertices, num_edges = load_graph(arquivo_gr)

    if transformar:
        graph = bounded_out_degree(graph, 2)

    print("n = {}, m = {}".format(num_vertices, num_edges))

    qt_executions = len(algorithms) * r
    current_execution = 0

    ref_dist = None
    for alg in algorithms:
        for i in range(r):

            current_execution += 1
            progress = (current_execution / qt_executions) * 100

            print(
                f"\rExecuted {progress:.2f}% "
                f"| arquivo: {os.path.basename(arquivo_gz)} "
                f"| algorithm: {alg.__name__} "
                f"| repetition: {i + 1}/{r}      ",
                end="",
                flush=True
            )

            source = 1
            start_time = process_time()
            dist = alg(graph, source)
            end_time = process_time()

            delta_time = end_time - start_time

            num_explored = sum(1 for v in dist if dist[v] < float('inf'))
            explored_percentage = (num_explored / num_vertices) * 100

            if alg == dijkstra:
                ref_dist = dist
                is_correct = True
                error_count = 0
            else:
                if ref_dist is None:
                    ref_dist = dijkstra(graph, source)
                error_count = sum(
                    1 for v, d in ref_dist.items()
                    if (dist.get(v, float('inf')) != d and abs(dist.get(v, float('inf')) - d) > 1e-9)
                )
                is_correct = (error_count == 0)

            file_results.append({
                "arquivo": os.path.basename(arquivo_gz),
                "num_vertices": num_vertices,
                "num_edges": num_edges,
                "algorithm": alg.__name__,
                "execution_time": delta_time,
                "repetition": i,
                "fully_reachable": is_fully_reachable(graph, source, num_vertices),
                "explored_percentage": explored_percentage,
                "is_correct": is_correct,
                "error_count": error_count
            })

    print()

    # Remover o arquivo descompactado
    os.remove(arquivo_gr)

    return file_results


parser = argparse.ArgumentParser(
    description="Executa testes comparativos em grafos DIMACS (.gz).",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument(
    "arquivo",
    type=str,
    help="Caminho de um arquivo .gz ou de um diretório contendo vários arquivos .gz."
)
parser.add_argument(
    "-r", "--repetitions",
    dest="r",
    type=int,
    required=True,
    help="Quantidade de repetições por algoritmo, sobre o mesmo grafo."
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
    "--transform",
    dest="transformar",
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
    help="Algoritmos a executar: dijkstra, sssp_duan_et_al, sssp_duan_et_al_iter, sssp_duan_et_al_opt."
)

args = parser.parse_args()

arquivo = args.arquivo
is_directory = os.path.isdir(arquivo)
r = args.r
salvar = args.salvar
transformar = args.transformar

# Algoritmos
ALGO_MAP = {
    "dijkstra": dijkstra,
    "sssp_duan_et_al": sssp_duan_et_al,
    "sssp_duan_et_al_iter": sssp_duan_et_al_iter,
    "sssp_duan_et_al_opt": sssp_duan_et_al_opt,
}
algorithms = tuple(ALGO_MAP[name] for name in args.algorithms)

# Monta a lista de arquivos .gz a processar
if is_directory:
    arquivos = sorted(glob.glob(os.path.join(arquivo, "*.gz")))
    if not arquivos:
        print(f"Nenhum arquivo .gz encontrado em '{arquivo}'.")
        exit(0)
else:
    arquivos = [arquivo]

results = []

for idx, arquivo_gz in enumerate(arquivos, start=1):
    if is_directory:
        print(f"\n[{idx}/{len(arquivos)}] Processando {os.path.basename(arquivo_gz)}")
    results.extend(process_file(arquivo_gz, r, algorithms, transformar))

print("\nExecution finished.")

if args.output_dir:
    dir = args.output_dir if args.output_dir.endswith(('/', '\\')) else args.output_dir + '/'
else:
    dir = "data/untracked_results/" if salvar == "--untrack" else "data/"

name = f"dimacs-results-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"

# Criar diretório se não existir
if not os.path.exists(dir):
    os.makedirs(dir)

# Salvar os resultados em CSV
with open(f'{dir}{name}.csv', 'w', newline='') as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "arquivo",
            "num_vertices",
            "num_edges",
            "algorithm",
            "execution_time",
            "repetition",
            "fully_reachable",
            "explored_percentage",
            "is_correct",
            "error_count"
        ]
    )

    writer.writeheader()
    writer.writerows(results)