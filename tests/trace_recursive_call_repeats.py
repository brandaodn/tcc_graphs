"""Diagnóstico de repetição dentro/entre chamadas recursivas.

Instrumente a variante experimental local atribuindo call_id crescente por
invocação de bmssp_frontier. Conte varreduras pelo contexto:
(vertex, order.key(vertex, dist), level, bound, next_bound, child_boundary).

Evite pular varreduras entre chamadas diferentes: a mesma assinatura de
limites não garante igualdade dos estados internos. Este arquivo documenta
as invariantes a medir e fornece uma função de classificação dos eventos.
"""


def classify_scans(events):
    """events: iterável de (call_id, context); retorna (within, across)."""
    seen = {}
    within = 0
    across = 0
    for call_id, context in events:
        previous = seen.setdefault(context, set())
        if call_id in previous:
            within += 1
        elif previous:
            across += 1
        previous.add(call_id)
    return {"within_call_repeats": within,
            "across_call_repeats": across}


def test_classifier():
    a = ("v", (0, 1, 2), 1, "B", "Bi", "Bp")
    b = ("w", (1, 2, 3), 1, "B", "Bi", "Bp")
    result = classify_scans([
        (1, a), (1, a), (2, a), (2, a), (3, b)])
    assert result == {"within_call_repeats": 2,
                      "across_call_repeats": 1}


if __name__ == "__main__":
    test_classifier()
    print("classifier: OK")
