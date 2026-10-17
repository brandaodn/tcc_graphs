"""Experimental total-key eligibility test, not a proof of paper equivalence.

When numerical distances tie, checking the candidate's complete key prevents
reuse of an existing strictly better label as though reached from the current
parent. The article instead assumes a global unique ordering of paths.
"""
def candidate_key(u, v, weight, db, order):
    return db[u] + weight, order.hops[u] + 1, order.rank(v)

def eligible_candidate(u, v, weight, db, order):
    return candidate_key(u, v, weight, db, order) <= order.key(v, db)
