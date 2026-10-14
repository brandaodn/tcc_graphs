# Avaliação Experimental de Algoritmos SSSP: Dijkstra vs. BMSSP (Duan et al.)

Este repositório contém os experimentos de comparação empírica de desempenho entre o algoritmo clássico de Dijkstra e o algoritmo sub-linear de caminhos mínimos de fonte única (SSSP) proposto por Duan et al. (BMSSP), desenvolvido como parte de Trabalho de Conclusão de Curso (TCC) em Ciência da Computação (BCC/CEFET-MG).

---

## 1. Algoritmos Implementados

Os algoritmos estão disponíveis no pacote `graphs`:

* **`dijkstra`** (`graphs/graphs.py`): Implementação clássica com fila de prioridade binária (`heapq`), servindo como linha de base (*baseline*).
* **`sssp_duan_et_al`** (`graphs/duan_et_al.py`): Implementação recursiva original do algoritmo BMSSP com relação de ordem total de caminhos e fila de prioridade em lote (`BatchPQ`).
* **`sssp_duan_et_al_iter`** (`graphs/duan_et_al_iter.py`): Versão iterativa do BMSSP utilizando pilha explícita de execução de *frames*, eliminando a recursão de chamadas em profundidade.
* **`sssp_duan_et_al_opt`** (`graphs/duan_et_al_opt.py`): Versão otimizada do BMSSP substituindo o gargalo de `BatchPQ` por `BatchPQFast` (remoção preguiçosa de chaves e inserção por busca binária).
* **`bounded_out_degree`** (`graphs/degree_reduction.py`): Transformação que reduz o grau de saída do grafo para um limite constante ($d_{out} \le 2$), conforme pré-requisito teórico do artigo.

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
│   └── degree_reduction.py # Redutor de grau de saída
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

Para aplicar a transformação de redução de grau em qualquer um dos scripts de teste, adicione a flag `--transform`.

---

## 5. Análise dos Resultados

Os notebooks na pasta `notebooks/` contêm a consolidação dos dados de cada bateria de testes, gráficos de distribuição de tempo (boxplots em escala logarítmica), comparação com e sem transformação de grau constante e fatores relativos de desempenho frente ao Dijkstra.

