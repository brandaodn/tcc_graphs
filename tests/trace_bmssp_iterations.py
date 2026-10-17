"""Instrumentação de iterações BMSSP (sem alterar código de produção).

Executar na raiz: python3 tests/trace_bmssp_iterations.py --case 21
Também: python3 tests/trace_bmssp_iterations.py --case path

Escreve JSONL de eventos e JSON de resumo em diagnostics/. Usa subprocesso
com timeout e orçamento de iterações. Eventos só descrevem estados observados;
repetição de estado não prova ausência de progresso matemático.
"""
import argparse
import json
import math
import multiprocessing as mp
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from graphs.graphs import Graph, dijkstra
import graphs.duan_et_al as rec
import graphs.duan_et_al_iter as itr
import graphs.duan_et_al_opt as opt


def build(case):
    g = Graph()
    if case == "path":
        n, source = 5, 0
        edges = [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]
    else:
        target = int(case)
        rng = random.Random(20261017)
        for index in range(target + 1):
            n = rng.randint(2, 16)
            probability = rng.choice([0.08, 0.2, 0.5])
            edges = [(u, v, rng.randint(0, 9))
                     for u in range(n) for v in range(n)
                     if u != v and rng.random() < probability]
            source = rng.randrange(n)
    for u in range(n):
        g.adj[u] = []
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g, source, edges


def encode(v):
    if isinstance(v, float) and math.isinf(v):
        return "inf" if v > 0 else "-inf"
    if isinstance(v, tuple):
        return [encode(x) for x in v]
    if isinstance(v, set):
        return sorted((encode(x) for x in v), key=repr)
    if isinstance(v, list):
        return [encode(x) for x in v]
    if isinstance(v, dict):
        return {str(k): encode(val) for k, val in v.items()}
    return v


def run_child(name, case, outdir, max_iterations):
    graph, source, edges = build(case)
    output = Path(outdir) / f"{case}_{name}.jsonl"
    stats_file = Path(outdir) / f"{case}_{name}_summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    algorithms = {
        "recursive": rec.sssp_duan_et_al,
        "iterative": itr.sssp_duan_et_al_iter,
        "optimized": opt.sssp_duan_et_al_opt,
    }
    # Trace line events at the recursive BMSSP / optimized BMSSP loop,
    # and at the iterative BMSSP_iter driver. No monkey patch of relax.
    watched = {
        "BMSSP": rec.BMSSP.__code__.co_filename,
        "BMSSP_opt": opt.BMSSP_opt.__code__.co_filename,
        "BMSSP_iter": itr.BMSSP_iter.__code__.co_filename,
    }
    iteration_lines = {}
    for function in (rec.BMSSP, opt.BMSSP_opt, itr.BMSSP_iter):
        # Extract line numbers by matching the Python source line; avoids
        # brittle absolute line numbers across future edits.
        import inspect
        lines, start = inspect.getsourcelines(function)
        iteration_lines[function.__name__] = {
            start + i for i, line in enumerate(lines)
            if "Bi, Si = " in line and ".pull()" in line or
               "if len(f.U) < f.limit and not f.D.is_empty()" in line
        }
    events = 0
    states = Counter()
    last_dist = None
    start_time = time.monotonic()
    outcome = "complete"
    observed = None

    with output.open("w", encoding="utf-8") as log:
        def tracer(frame, event, arg):
            nonlocal events, last_dist
            if event != "line" or frame.f_code.co_name not in watched:
                return tracer
            fn = frame.f_code.co_name
            if frame.f_lineno not in iteration_lines.get(fn, ()):
                return tracer
            loc = frame.f_locals
            f = loc.get("f")
            level = loc.get("l", getattr(f, "l", None))
            D = loc.get("D", getattr(f, "D", None))
            U = loc.get("U", getattr(f, "U", set()))
            B = loc.get("B_key", getattr(f, "B", None))
            bprime = loc.get("B_prime", getattr(f, "B_prime", None))
            db = loc.get("db", {})
            active = getattr(D, "_key_val", {}) if D is not None else {}
            distances = tuple(sorted(((repr(k), repr(v)) for k, v in db.items())))
            fingerprint = repr((fn, level, B, bprime, tuple(sorted(map(repr, U))),
                                tuple(sorted((repr(k), repr(v)) for k, v in active.items())),
                                distances))
            states[fingerprint] += 1
            events += 1
            payload = {
                "event": events, "function": fn, "line": frame.f_lineno,
                "level": level, "B": encode(B), "B_prime": encode(bprime),
                "Bi": encode(loc.get("Bi", getattr(f, "Bi", None))),
                "B_i_prime": encode(loc.get("B_i_prime")),
                "Si": encode(loc.get("Si", getattr(f, "Si", None))),
                "Ui": encode(loc.get("Ui")),
                "U": encode(U), "queue": encode(active),
                "distances": encode(dict(db)),
                "same_state_count": states[fingerprint],
                "distances_changed": distances != last_dist,
            }
            last_dist = distances
            log.write(json.dumps(payload, ensure_ascii=False) + "\n")
            if events % 100 == 0:
                log.flush()
            if events >= max_iterations:
                raise RuntimeError(f"iteration budget exceeded: {max_iterations}")
            return tracer

        try:
            sys.settrace(tracer)
            observed = algorithms[name](graph, source)
        except Exception as exc:
            outcome = f"{type(exc).__name__}: {exc}"
        finally:
            sys.settrace(None)

    expected = dijkstra(graph, source)
    errors = None if observed is None else {
        str(v): {"expected": encode(d), "observed": encode(observed.get(v, math.inf))}
        for v, d in expected.items() if observed.get(v, math.inf) != d
    }
    stats = {
        "algorithm": name, "case": case, "vertices": len(graph.adj),
        "edges": len(edges), "source": source,
        "outcome": outcome, "events": events,
        "repeated_states": sum(c - 1 for c in states.values()),
        "most_repeated_state_count": max(states.values(), default=0),
        "elapsed_seconds": time.monotonic() - start_time,
        "distance_errors": errors,
        "trace_file": str(output),
    }
    stats_file.write_text(json.dumps(stats, indent=2, ensure_ascii=False),
                          encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="21")
    parser.add_argument("--timeout", type=float, default=6.0)
    parser.add_argument("--max-iterations", type=int, default=3000)
    parser.add_argument("--output-dir", default="diagnostics")
    args = parser.parse_args()
    for name in ("recursive", "iterative", "optimized"):
        p = mp.Process(target=run_child,
                       args=(name, args.case, args.output_dir, args.max_iterations))
        p.start()
        p.join(args.timeout)
        if p.is_alive():
            p.terminate()
            p.join()
            print(f"{name}: TIMEOUT; consultar JSONL parcial")
        else:
            summary = Path(args.output_dir) / f"{args.case}_{name}_summary.json"
            if summary.exists():
                x = json.loads(summary.read_text(encoding="utf-8"))
                print(f"{name}: {x['outcome']}; iteracoes={x['events']}; "
                      f"estados repetidos={x['repeated_states']}; "
                      f"divergencias={len(x['distance_errors'] or {})}")
            else:
                print(f"{name}: exitcode={p.exitcode}, sem resumo")


if __name__ == "__main__":
    main()
