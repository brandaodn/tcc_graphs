# BMSSP fiel ao artigo: auditoria inicial (etapa 1)

Fonte normativa: Duan, Mao, Mao, Shu, Yin, *Breaking the Sorting Barrier for Directed Single-Source Shortest Paths*, arXiv:2504.17033v2 (30 julho 2025), https://arxiv.org/html/2504.17033v2

Escopo: auditoria estática do código da branch `db-avaliacoes`, **não é uma implementação validada**. Não substituir `graphs/duan_et_al.py` nem a variante experimental por esta documentação.

## Divergências já verificadas

| Prioridade | Pseudocódigo | Código atual | Consequência |
|---|---|---|---|
| P0 | Algoritmo 3, linha 12: parar quando `|U| >= k * 2^(l*t)` | `graphs/duan_et_al.py`: usa `k**2 * 2**(l*t)` | Violação explícita da cota de trabalho usada na demonstração |
| P0 | Algoritmo 3, linha 19, inclui igualdade no relaxamento `d[u]+w <= d[v]` | `BMSSP`: insere na fila apenas se `accepted=True` | Pode perder trabalho de fronteira, mesmo com rótulo igual |
| P0 | Lema 3.3: `BatchPrepend(L)` requer novos valores menores que quaisquer valores vigentes; `Pull` devolve os menores e limite separador | `BatchPQ`: blocos mutáveis, lazy deletion e `_min_remaining_val` baseado nos primeiros blocos | Precisamos provar/testar preservação do contrato após diminuição de chave |
| P0 | Seção 2: transformar grafo para graus de entrada/saída constantes antes da análise | `sssp_duan_et_al`: recebe grafo original com graus arbitrários | Limite assintótico demonstrado não se aplica diretamente ao código atual |
| P1 | Seção 2: desempate por (comprimento, saltos, sequência reversa de vértices) | `TotalOrder` usa (distância, saltos, rank do vértice); predecessor participa apenas do desempate em `relax` | Exige verificação de consistência ao atualizar rótulos e predecessores |
| P1 | Algoritmo 1: conjunto `W_i` vem somente de arestas com candidato <= rótulo anterior e < B | `find_pivots` inclui vértice com `key_v < B`, independentemente de candidato pior | Pode aumentar `W` e afetar escolha dos pivôs |
| P1 | Algoritmo 3 devolve apenas `(B_prime,U)` com vértices completos; intervalos são estritos | `quota_pending_probe` devolve `pending` extra e processa suas arestas | Variante não é a implementação coberta pelo teorema |
| P1 | `l=ceil(log n/t)`, `k=floor(log^(1/3)n)`, `t=floor(log^(2/3)n)` (log conforme texto) | implementação força `k,t>=2`, e usa `floor(log2(n)/t)+1` | Diferenças nas cotas e níveis, principalmente em potências exatas |
| P2 | algoritmo 2: heap suporta decrease-key e evita entradas obsoletas | `base_case`: heap com inserções repetidas e filtro de obsolescência | Correção precisa ser verificada; custo pode divergir |

## Invariantes a validar antes de otimizar

1. `BaseCase` exige `S={x}`, e `x` completo.
2. Em todo `BMSSP(l,B,S)`: `|S|<=2^(l*t)` e `B>max(dhat[S])`.
3. No retorno: `B_prime<=B`; `U` contém somente vértices completos; sucesso implica `B_prime=B`.
4. Se a execução é parcial, a fronteira não perde caminhos para vértices com distância real abaixo de `B_prime`.
5. `BatchPrepend`: suas entradas são menores que os valores ainda na estrutura, após atualização por chaves.
6. Os conjuntos `U_i` das chamadas filhas de mesmo pai são disjuntos (necessário para análise de custo).
7. Grafos são dirigidos e pesos não negativos. A transformação para grau constante precisa preservar as distâncias originais.

## Plano de execução

1. Regressões *estáticas* para as divergências P0; não alterar a implementação legada silenciosamente.
2. Criar módulo `graphs/duan_et_al_faithful.py` independente, inicialmente como esqueleto que rejeite uso incompleto.
3. Implementar transformação de grau constante e testes diferenciais contra Dijkstra.
4. Construir `BatchPQ` de referência com o contrato do Lema 3.3; testes com operações válidas e decrease-key.
5. Transcrever Algoritmos 1, 2 e 3 e testar invariantes recursivas; só depois medir desempenho.
6. Benchmark pareado Python: Dijkstra `heapq`, BMSSP fiel, BMSSP experimental; mesmos grafos/sementes, warm-up, múltiplas repetições, tempos/contadores/correção.

**Não declarar `O(m log^(2/3)n)` para nenhuma versão enquanto não forem demonstradas as pré-condições e custos das estruturas.**
