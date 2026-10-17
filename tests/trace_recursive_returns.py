"""Rastreia retorno de filhos e classificação D/K em BMSSP sem alterar produção.

python3 tests/trace_recursive_returns.py --case path
python3 tests/trace_recursive_returns.py --case 21 --timeout 6

Saída: diagnostics/returns_<case>_<algorithm>.jsonl, e *_summary.json.
O rastreamento identifica linhas pelo conteúdo do fonte, evitando depender
de numeração fixa. Registra snapshots antes/depois das operações e eventos
de retorno. NÃO modifica parâmetros ou valores retornados.
"""
import argparse
import inspect
import json
import math
import multiprocessing as mp
import random
import sys
import time
from pathlib import Path

from graphs.graphs import Graph, dijkstra
import graphs.duan_et_al as recursive
import graphs.duan_et_al_iter as iterative
import graphs.duan_et_al_opt as optimized


def graph_for(case):
    rng = random.Random(20261017)
    if case == "path":
        n, source = 5, 0
        edges = [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]
    else:
        index = int(case)
        for _ in range(index + 1):
            n = rng.randint(2, 16)
            probability = rng.choice([0.08, 0.2, 0.5])
            edges = [(u, v, rng.randint(0, 9))
                     for u in range(n) for v in range(n)
                     if u != v and rng.random() < probability]
            source = rng.randrange(n)
    graph = Graph()
    for vertex in range(n):
        graph.adj[vertex] = []
    for u, v, w in edges:
        graph.add_edge(u, v, w)
    return graph, source, edges


def serial(x):
    if isinstance(x, float) and math.isinf(x):
        return "Infinity" if x > 0 else "-Infinity"
    if isinstance(x, (tuple, list, set)):
        values = sorted(x, key=repr) if isinstance(x, set) else x
        return [serial(v) for v in values]
    if isinstance(x, dict):
        return {str(k): serial(v) for k, v in x.items()}
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    return repr(x)


def watched_lines(func):
    lines, start = inspect.getsourcelines(func)
    targets = {}
    for offset, line in enumerate(lines):
        stripped = line.strip()
        if (("B_i_prime, Ui =" in stripped) or
            ("U |= Ui" in stripped) or ("f.U |= Ui" in stripped) or
            ("D.batch_prepend(" in stripped) or
            ("f.B_prime =" in stripped) or
            ("B_prime = min(B_i_prime" in stripped) or
            ("return B_prime, U" in stripped) or
            ("ret = (f.B_prime, f.U)" in stripped)):
            targets[start + offset] = stripped
    return targets


def worker(case, algorithm, folder, budget):
    graph, source, edges = graph_for(case)
    functions = {
        "recursive": recursive.sssp_duan_et_al,
        "iterative": iterative.sssp_duan_et_al_iter,
        "optimized": optimized.sssp_duan_et_al_opt,
    }
    targets = {}
    for fn in (recursive.BMSSP, iterative.BMSSP_iter, iterative._absorb,
               optimized.BMSSP_opt, recursive.base_case):
        targets[fn.__code__] = watched_lines(fn)
    path = Path(folder) / f"returns_{case}_{algorithm}.jsonl"
    summary = Path(folder) / f"returns_{case}_{algorithm}_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = 0
    outcome = "completed"
    result = None
    started = time.monotonic()

    with path.open("w", encoding="utf-8", buffering=1) as file:
        def trace(frame, event, argument):
            nonlocal seen
            code = frame.f_code
            if code not in targets:
                return None
            if event == "line" and frame.f_lineno not in targets[code]:
                return trace
            if event not in ("line", "return"):
                return trace
            loc = frame.f_locals
            f = loc.get("f")
            queue = loc.get("D", getattr(f, "D", None))
            data = {
                "event": event,
                "function": code.co_name,
                "line": frame.f_lineno,
                "checkpoint": targets[code].get(frame.f_lineno, "function_return"),
                "level": loc.get("l", getattr(f, "l", None)),
                "B": serial(loc.get("B_key", loc.get("B", getattr(f, "B", None)))),
                "Bi": serial(loc.get("Bi", getattr(f, "Bi", None))),
                "B_i_prime": serial(loc.get("B_i_prime")),
                "B_prime": serial(loc.get("B_prime", getattr(f, "B_prime", None))),
                "Si": serial(loc.get("Si", getattr(f, "Si", None))),
                "Ui": serial(loc.get("Ui")),
                "U": serial(loc.get("U", getattr(f, "U", None))),
                "K": serial(loc.get("K")),
                "prepend_items": serial(loc.get("prepend_items")),
                "queue_keys": serial(dict(getattr(queue, "_key_val", {}))),
                "distances": serial(dict(loc.get("db", {}))),
            }
            if event == "return":
                data["returned"] = serial(argument)
            seen += 1
            data["seq"] = seen
            file.write(json.dumps(data, ensure_ascii=False) + "\n")
            if seen >= budget:
                raise RuntimeError(f"trace budget exceeded: {budget}")
            return trace

        try:
            sys.settrace(trace)
            result = functions[algorithm](graph, source)
        except Exception as exc:
            outcome = f"{type(exc).__name__}: {exc}"
        finally:
            sys.settrace(None)

    reference = dijkstra(graph, source)
    differences = None if result is None else {
        str(v): {"expected": serial(expected),
                 "actual": serial(result.get(v, math.inf))}
        for v, expected in reference.items()
        if result.get(v, math.inf) != expected
    }
    summary.write_text(json.dumps({
        "case": case, "algorithm": algorithm, "source": source,
        "n": len(graph.adj), "m": len(edges),
        "outcome": outcome, "events": seen,
        "elapsed_s": round(time.monotonic() - started, 5),
        "differences": differences, "trace": str(path)
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="path")
    parser.add_argument("--timeout", type=float, default=6)
    parser.add_argument("--max-events", type=int, default=5000)
    parser.add_argument("--output-dir", default="diagnostics")
    args = parser.parse_args()
    if args.timeout <= 0 or args.max_events <= 0:
        parser.error("timeout e max-events devem ser positivos")
    for algorithm in ("recursive", "iterative", "optimized"):
        process = mp.Process(target=worker, args=(
            args.case, algorithm, args.output_dir, args.max_events))
        process.start()
        process.join(args.timeout)
        if process.is_alive():
            process.terminate()
            process.join()
            print(f"{algorithm}: TIMEOUT; JSONL parcial disponível")
            continue
        summary = Path(args.output_dir) / (
            f"returns_{args.case}_{algorithm}_summary.json")
        if summary.exists():
            data = json.loads(summary.read_text(encoding="utf-8"))
            print(f"{algorithm}: {data['outcome']}; "
                  f"eventos={data['events']}; "
                  f"divergências={len(data['differences'] or {})}")
        else:
            print(f"{algorithm}: sem resumo, exitcode={process.exitcode}")


if __name__ == "__main__":
    main()
