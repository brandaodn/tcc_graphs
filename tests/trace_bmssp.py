"""Instrumentacao nao invasiva do BMSSP no caso aleatorio 21.

Uso (a partir da raiz do repositorio):
    python3 tests/trace_bmssp.py --case 21 --timeout 8 --max-lines 150000

Cria logs em diagnostics/ (ou --output-dir). Nao modifica algoritmos.
O timeout e o limite de linhas sao mecanismos de protecao, nao provas de loop infinito.
"""
import argparse
from collections import Counter, deque
import json
import multiprocessing as mp
from pathlib import Path
import random
import sys
import time
import traceback


ALGORITHMS = (
    "sssp_duan_et_al",
    "sssp_duan_et_al_iter",
    "sssp_duan_et_al_opt",
)
FOCUS = {"BMSSP", "BMSSP_iter", "BMSSP_opt", "base_case",
         "find_pivots", "_open_frame", "_absorb", "pull",
         "batch_prepend", "insert", "relax"}


def build_case(index):
    # Repete exatamente o consumo do RNG em test_random_small_graphs.
    from graphs.graphs import Graph
    rng = random.Random(20261017)
    for case in range(index + 1):
        n = rng.randint(2, 16)
        probability = rng.choice([0.08, 0.2, 0.5])
        edges = [(u, v, rng.randint(0, 9))
                 for u in range(n) for v in range(n)
                 if u != v and rng.random() < probability]
        source = rng.randrange(n)
    graph = Graph()
    for v in range(n):
        graph.adj[v] = []
    for u, v, w in edges:
        graph.add_edge(u, v, w)
    return graph, {"case": index, "seed": 20261017,
                   "n": n, "p": probability, "source": source,
                   "edges": edges}


def short(value):
    if isinstance(value, (set, list, tuple, dict)):
        return {"type": type(value).__name__, "length": len(value),
                "sample": repr(list(value)[:5] if isinstance(value, (set, dict))
                               else value[:5])[:180]}
    return repr(value)[:160]


def worker(name, case, max_lines, output):
    from graphs import (sssp_duan_et_al, sssp_duan_et_al_iter,
                        sssp_duan_et_al_opt)
    from graphs.graphs import dijkstra
    graph, spec = build_case(case)
    methods = dict(zip(ALGORITHMS, (sssp_duan_et_al,
                                   sssp_duan_et_al_iter,
                                   sssp_duan_et_al_opt)))
    baseline = dijkstra(graph, spec["source"])
    counters = Counter()
    recent = deque(maxlen=80)
    calls = Counter()
    depth = 0
    lines = 0
    started = time.monotonic()
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "complete"
    result = None

    def tracer(frame, event, arg):
        nonlocal lines, depth
        filename = frame.f_code.co_filename.replace("\\", "/")
        if "/graphs/" not in filename:
            return tracer
        fn = frame.f_code.co_name
        if event == "call":
            depth += 1
            calls[fn] += 1
            if fn in FOCUS:
                loc = frame.f_locals
                fields = {k: short(loc[k]) for k in
                          ("l", "B_key", "B", "S", "Bi", "Si", "B_prime",
                           "U", "M", "vertex", "key") if k in loc}
                recent.append({"event": "call", "function": fn,
                               "depth": depth, "line": frame.f_lineno,
                               "state": fields})
        elif event == "return":
            if fn in FOCUS:
                recent.append({"event": "return", "function": fn,
                               "depth": depth, "line": frame.f_lineno,
                               "value": short(arg)})
            depth = max(depth - 1, 0)
        elif event == "line":
            lines += 1
            counters[f"{Path(filename).name}:{frame.f_lineno}:{fn}"] += 1
            if lines >= max_lines:
                raise RuntimeError(f"TRACE_LINE_LIMIT: {max_lines}")
        return tracer

    try:
        sys.settrace(tracer)
        result = methods[name](graph, spec["source"])
    except Exception as exc:
        status = f"{type(exc).__name__}: {exc}"
        recent.append({"event": "exception", "traceback": traceback.format_exc()[-2500:]})
    finally:
        sys.settrace(None)
        elapsed = time.monotonic() - started
        # Distancias podem ser inf: serializar como strings para JSON estrito.
        def safe_dist(d):
            return {str(k): ("inf" if v == float("inf") else v)
                    for k, v in d.items()}
        report = {"algorithm": name, "status": status, "elapsed_seconds": elapsed,
                  "case": spec, "traced_lines": lines,
                  "calls": dict(calls),
                  "hot_lines": counters.most_common(25),
                  "recent_events": list(recent),
                  "baseline": safe_dist(baseline),
                  "actual": safe_dist(result) if result is not None else None}
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False,
                                   allow_nan=False), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case", type=int, default=21)
    p.add_argument("--timeout", type=float, default=8.0)
    p.add_argument("--max-lines", type=int, default=150000)
    p.add_argument("--output-dir", default="diagnostics")
    args = p.parse_args()
    if args.case < 0 or args.timeout <= 0 or args.max_lines < 1:
        p.error("case >= 0, timeout > 0 e max-lines >= 1 sao obrigatorios")
    graph, spec = build_case(args.case)
    print(f"Caso {args.case}: n={spec['n']} m={len(spec['edges'])} "
          f"p={spec['p']} source={spec['source']}", flush=True)
    for algorithm in ALGORITHMS:
        output = Path(args.output_dir) / f"bmssp_case{args.case}_{algorithm}.json"
        proc = mp.Process(target=worker,
                          args=(algorithm, args.case, args.max_lines, str(output)))
        proc.start()
        proc.join(args.timeout)
        if proc.is_alive():
            proc.terminate()
            proc.join(2)
            if proc.is_alive():
                proc.kill()
                proc.join()
            print(f"{algorithm}: TIMEOUT ({args.timeout}s); sem relatorio parcial "
                  "(o processo foi interrompido)", flush=True)
        elif output.exists():
            report = json.loads(output.read_text(encoding="utf-8"))
            print(f"{algorithm}: {report['status']}; "
                  f"{report['traced_lines']} linhas; log: {output}", flush=True)
            for location, n in report["hot_lines"][:5]:
                print(f"  hotspot {location}: {n}", flush=True)
        else:
            print(f"{algorithm}: terminou sem gerar log (exitcode={proc.exitcode})",
                  flush=True)


if __name__ == "__main__":
    main()
