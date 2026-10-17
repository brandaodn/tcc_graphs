"""Fail-fast assertions for BMSSP recursion contracts.

These diagnostics do not fix the algorithm. Intended for before-BaseCase
instrumentation and differential testing against Dijkstra.
"""
class BMSSPContractViolation(RuntimeError):
    pass

def check_child_entry(*, level, bound, sources, labels, order, parent_bound=None, batch_size=None):
    if not sources:
        raise BMSSPContractViolation("empty recursive frontier")
    if any(order.key(x, labels) >= bound for x in sources):
        raise BMSSPContractViolation(
            f"level={level} source key violates strict bound: "
            f"{[(x, order.key(x, labels)) for x in sources]} >= {bound}")
    if parent_bound is not None and bound > parent_bound:
        raise BMSSPContractViolation(
            f"level={level} child bound {bound} exceeds parent {parent_bound}")
    if batch_size is not None and len(sources) > batch_size:
        raise BMSSPContractViolation(
            f"level={level} source cardinality {len(sources)} > {batch_size}")

def check_base_case_result(*, seed, bound, returned_bound, completed, labels, order):
    if returned_bound > bound:
        raise BMSSPContractViolation("BaseCase returned an increasing bound")
    if any(order.key(v, labels) >= returned_bound for v in completed):
        raise BMSSPContractViolation("BaseCase returned a vertex outside exclusive boundary")
    if seed not in completed and returned_bound <= order.key(seed, labels):
        raise BMSSPContractViolation(
            f"nonprogress: seed={seed} key={order.key(seed, labels)}, "
            f"B={bound}, B_prime={returned_bound}, U={sorted(map(str, completed))}; "
            "check completeness of seed and stale labels before BaseCase")
