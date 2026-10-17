import math
import unittest
from collections import defaultdict
from graphs.graphs import Graph
from graphs.batch_pq import TotalOrder
from graphs.duan_et_al_faithful_components import base_case_faithful, find_pivots_faithful


class FaithfulComponentsTests(unittest.TestCase):
    def setup_path(self):
        g = Graph()
        for u in range(5):
            g.adj[u] = []
        for u,v,w in ((0,1,2),(1,2,3),(2,3,4),(3,4,5)):
            g.add_edge(u,v,w)
        db = defaultdict(lambda: math.inf)
        db[0] = 0
        order = TotalOrder()
        order.rank(0)
        return g,db,order

    def test_base_exclusive_boundary(self):
        g,db,order = self.setup_path()
        B,U=base_case_faithful(g,order.TOP,{0},db,2,order)
        self.assertEqual(U,{0,1})
        self.assertEqual(B,order.key(2,db))

    def test_base_requires_singleton(self):
        g,db,order = self.setup_path()
        with self.assertRaises(ValueError):
            base_case_faithful(g,order.TOP,{0,1},db,2,order)

    def test_find_pivots_path(self):
        g,db,order = self.setup_path()
        P,W=find_pivots_faithful(g,order.TOP,{0},db,2,order)
        self.assertEqual(P,{0})
        self.assertEqual(W,{0,1,2})

    def test_candidate_strictly_worse_is_not_added(self):
        g=Graph()
        for v in range(3):
            g.adj[v]=[]
        g.add_edge(0,2,9)
        db=defaultdict(lambda: math.inf,{0:0,2:1})
        order=TotalOrder()
        order.rank(0)
        P,W=find_pivots_faithful(g,order.TOP,{0},db,1,order)
        self.assertNotIn(2,W)

    def test_zero_weight_cycle_terminates(self):
        g=Graph()
        for v in range(3):g.adj[v]=[]
        g.add_edge(0,1,0);g.add_edge(1,0,0);g.add_edge(1,2,0)
        db=defaultdict(lambda:math.inf,{0:0})
        order=TotalOrder();order.rank(0)
        B,U=base_case_faithful(g,order.TOP,{0},db,2,order)
        self.assertLessEqual(len(U),2)
        self.assertEqual(db[2],0)


if __name__ == "__main__":
    unittest.main()
