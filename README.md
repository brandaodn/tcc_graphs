# Avaliação Experimental de Algoritmos SSSP: Dijkstra vs. BMSSP (Duan et al.)

Este repositório contém os experimentos de comparação empírica de desempenho entre o algoritmo clássico de Dijkstra e o algoritmo sub-linear de caminhos mínimos de fonte única (SSSP) proposto por Duan et al. (BMSSP), desenvolvido como parte de Trabalho de Conclusão de Curso (TCC) em Ciência da Computação (BCC/CEFET-RJ).

---

## 1. Algoritmos Implementados

Os algoritmos estão disponíveis no pacote `graphs`:

* **`dijkstra`** (`graphs/graphs.py`): Implementação clássica com fila de prioridade binária (`heapq`), servindo como linha de base (*baseline*).
* **`sssp_duan_et_al`** (`graphs/duan_et_al.py`): Implementação recursiva original do algoritmo BMSSP com relação de ordem total de caminhos e fila de prioridade em lote (`BatchPQ`).
* **`sssp_duan_et_al_iter`** (`graphs/duan_et_al_iter.py`): Versão iterativa do BMSSP utilizando pilha explícita de execução de *frames*, eliminando a recursão de chamadas em profundidade.
* **`sssp_duan_et_al_opt`** (`graphs/duan_et_al_opt.py`): Versão otimizada do BMSSP substituindo o gargalo de `BatchPQ` por `BatchPQFast` (remoção preguiçosa de chaves e inserção por busca binária).
* **`sssp_duan_et_al_fast`** (`graphs/duan_et_al_fast.py`): Mesmo algoritmo da versão otimizada, com representação de baixo custo para Python (vértices renumerados, `db`/`hops`/`pred` em listas e relaxamento sem chamadas de método). Serve como "melhor caso" do BMSSP em Python; a versão fiel ao artigo continua sendo a referência.
* **`bounded_out_degree`** (`graphs/degree_reduction.py`): Transformação que limita apenas o grau de saída ($d_{out} \le 2$), substituindo cada vértice de grau alto por uma cadeia de vértices auxiliares ligados por arestas de peso zero.
* **`constant_degree`** (`graphs/degree_reduction.py`): Transformação descrita no artigo (Seção 2, *Constant-Degree Graph*): cada vértice $v$ vira um ciclo de arestas de peso zero com um vértice $x_{vw}$ para cada vizinho $w$, e cada aresta $(u, v)$ vira $x_{uv} \to x_{vu}$. Garante grau de entrada **e** de saída $\le 2$, com $O(m)$ vértices e arestas.

---

## 2. Estrutura de Diretórios

```text
.
├── graphs/             # Módulo com implementações dos algoritmos e estruturas
│   ├── graphs.py           # Classe Graph, I/O e Dijkstra
│   ├── batch_pq.py         # Estruturas de dados (TotalOrder, BatchPQ e BatchPQFast)
│   ├── duan_et_al.py       # BMSSP recursivo
│   ├── duan_et_al_iter.py  # BMSSP iterativo
│   ├── duan_et_al_opt.py   # BMSSP com BatchPQ otimizada
│   ├── duan_et_al_fast.py  # BMSSP otimizado com listas indexadas (melhor caso)
│   └── degree_reduction.py # Reduções de grau (bounded_out_degree e constant_degree)
├── notebooks/          # Notebooks Jupyter de consolidação e análise estatística
│   ├── lote1-analise.ipynb # Resultados do Lote 1 (Dijkstra vs BMSSP recursivo)
│   ├── lote2-analise.ipynb # Resultados do Lote 2 (inclusão do BMSSP iterativo)
│   ├── lote3-analise.ipynb # Resultados do Lote 3 (inclusão do BMSSP otimizado)
│   └── analysis.ipynb      # Análises exploratórias preliminares
├── data/               # Dados gerados pelos experimentos
│   ├── lote1-tcc2/         # Grafos sintéticos e CSVs do lote 1
│   ├── lote2-tcc2/         # Grafos sintéticos e CSVs do lote 2
│   ├── lote3-tcc2/         # Grafos sintéticos e CSVs do lote 3
│   └── legacy/             # Resultados preliminares arquivados
├── input_graphs/       # Instâncias reais de redes viárias (DIMACS 9th Challenge)
├── tests/              # Testes de corretude contra o Dijkstra
├── generate_graphs.py  # Gerador de instâncias sintéticas G(n, p)
├── random_test.py      # Execução de testes em grafos sintéticos
├── dimacs_test.py      # Execução de testes em instâncias DIMACS
├── routine.sh          # Pipeline automatizado de execução de lotes
└── requirements.txt    # Dependências do projeto
```

---

## 3. Instalação e Requisitos

Requer Python 3.10 ou superior.

```bash
# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

---

## 4. Como Executar os Experimentos

### 4.1. Execução Automatizada (Pipeline Completo)

O script `routine.sh` automatiza a geração dos grafos sintéticos, execução com e sem redução de grau e gravação dos relatórios em CSV:

```bash
chmod +x routine.sh
./routine.sh
```

### 4.2. Execuções Individuais

* **Gerar instâncias sintéticas:**
  ```bash
  python generate_graphs.py --path data/graphs --vertices 10000 50000 --num-graphs 5
  ```

* **Rodar experimentos em grafos sintéticos:**
  ```bash
  python random_test.py --track --mode load --path data/graphs --executions-per-graph 5
  ```

* **Rodar experimentos nas redes viárias DIMACS:**
  ```bash
  python dimacs_test.py input_graphs/ -r 5 --track
  ```

Para aplicar uma redução de grau em qualquer um dos scripts de teste, use a flag `--transform`:

* `--transform` (ou `--transform out`): `bounded_out_degree`, que limita só o grau de saída;
* `--transform cycle`: `constant_degree`, a transformação do artigo, com grau de entrada e de saída $\le 2$.

A coluna `transform` dos CSVs registra o modo usado (`none`, `out` ou `cycle`), e `explored_percentage` conta apenas os vértices do grafo original.

Os CSVs registram dois tempos por execução: `execution_time` (tempo de CPU, via `process_time`) e `wall_time` (tempo de parede, via `perf_counter`).

### 4.3. Reconstrução do Caminho Mínimo

Por padrão, as funções `sssp_duan_et_al*` retornam apenas as distâncias. Com `return_pred=True`, retornam também os predecessores, e `shortest_path` reconstrói o caminho até qualquer vértice (em termos do grafo original, removendo os vértices auxiliares criados por `bounded_out_degree` e `constant_degree`):

```python
from graphs import load_graph, sssp_duan_et_al_opt, shortest_path

g = load_graph("data/lote3-tcc2/graphs/n10000k3.00i0.json")
dist, pred = sssp_duan_et_al_opt(g, 0, return_pred=True)
print(dist[42], shortest_path(pred, 0, 42))  # None se 42 não for alcançável
```

### 4.4. Testes de Corretude

Compara as distâncias de todas as versões do BMSSP com as do Dijkstra em milhares de grafos aleatórios pequenos:

```bash
python -m unittest discover tests
```

---

## 5. Análise dos Resultados

Os notebooks na pasta `notebooks/` contêm a consolidação dos dados de cada bateria de testes, gráficos de distribuição de tempo (boxplots em escala logarítmica), comparação com e sem transformação de grau constante e fatores relativos de desempenho frente ao Dijkstra.

