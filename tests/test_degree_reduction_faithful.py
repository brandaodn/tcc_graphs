"""SSSP distance and degree invariants for faithful directed reduction."""
import math
import random
import unittest
from graphs.graphs import Graph, dijkstra
from graphs.degree_reduction_faithful import reduce_to_degree_two

class DegreeReductionFaithfulTests(unittest.TestCase):
    def verify(self, g, n, sources):
        reduced = reduce_to_degree_two(g, vertices=range(n))
        indeg = {v:0 for v in reduced.graph.adj}
        for u, edges in reduced.graph.adj.items():
            self.assertLessEqual(len(edges),2)
            for v,w in edges:
                indeg[v]+=1
                self.assertGreaterEqual(w,0)
        self.assertTrue(all(d<=2 for d in indeg.values()))
        self.assertLessEqual(len(reduced.graph.adj),2*reduced.original_edges+n)
        for s in sources:
            expected = dijkstra(g,s)
            observed = reduced.project_distances(
                dijkstra(reduced.graph,reduced.representative[s]))
            for v in range(n):
                self.assertEqual(observed[v],expected.get(v,math.inf),
                                 f"source={s}, target={v}")

    def test_parallel_loops_and_isolates(self):
        g=Graph()
        for u,v,w in [(0,1,3),(0,1,1),(1,1,0),(2,0,4)]:
            g.add_edge(u,v,w)
        self.verify(g,5,range(5))

    def test_high_degree_zero_cycles(self):
        g=Graph()
        for v in range(1,50):
            g.add_edge(0,v,v%3)
            g.add_edge(v,0,0)
        self.verify(g,52,(0,1,17,49,51))

    def test_seeded_random(self):
        rng=random.Random(20261017)
        for n in (2,8,16,32):
            for p in (.03,.25,.7):
                for mode in ("zero","small","positive"):
                    g=Graph()
                    for u in range(n):
                        g.adj[u]=[]
                        for v in range(n):
                            if rng.random()<p:
                                w=0 if mode=="zero" else (
                                    rng.randint(0,2) if mode=="small"
                                    else rng.randint(1,20))
                                g.add_edge(u,v,w)
                    with self.subTest(n=n,p=p,mode=mode):
                        self.verify(g,n,(0,n//2,n-1))

    def test_negative_rejected(self):
        g=Graph()
        g.add_edge(0,1,-1)
        with self.assertRaises(ValueError):
            reduce_to_degree_two(g)
if __name__=="__main__":
    unittest.main()
