"""Regression: a BaseCase call with an out-of-order frontier seed stalls.

This is a diagnostic test for the current partial reconstruction, not a
proof that the article's BaseCase allows such inputs.
"""
import unittest
from collections import defaultdict
from graphs.graphs import Graph
from graphs.batch_pq import TotalOrder
from graphs.duan_et_al_faithful_components import base_case_faithful

class BaseCaseSeedOrderingRegression(unittest.TestCase):
    def test_out_of_order_seed_can_be_excluded_from_U(self):
        graph=Graph()
        for v in (1,20,27):
            graph.adj[v]=[]
        graph.add_edge(1,20,0)
        graph.add_edge(1,27,0)
        db=defaultdict(lambda:float('inf'),{1:1,20:1,27:1})
        order=TotalOrder()
        for v in (1,20,27):
            order.rank(v)
        order.hops[1]=5
        order.hops[20]=3
        order.hops[27]=3
        initial=order.key(1,db)
        B=order.TOP
        returned,U=base_case_faithful(graph,B,{1},db,2,order)
        self.assertEqual(U,{20,27})
        self.assertEqual(returned,initial)
        self.assertNotIn(1,U)
        self.assertLessEqual(returned,initial)

if __name__ == '__main__':
    unittest.main()
