import unittest
from collections import defaultdict
from graphs.batch_pq import TotalOrder
from graphs.bmssp_total_key_guard import candidate_key, eligible_candidate

class TotalKeyGuardTests(unittest.TestCase):
    def test_numeric_tie_with_worse_hops_rejected(self):
        db=defaultdict(lambda:float('inf'),{1:1,20:1})
        order=TotalOrder()
        order.rank(1);order.rank(20)
        order.hops[1]=5
        order.hops[20]=3
        self.assertEqual(db[1]+0,db[20])
        self.assertFalse(eligible_candidate(1,20,0,db,order))

    def test_numeric_improvement_accepted(self):
        db=defaultdict(lambda:float('inf'),{1:1,20:4})
        order=TotalOrder()
        order.hops[1]=5
        self.assertTrue(eligible_candidate(1,20,0,db,order))

    def test_equal_key_candidate_accepted(self):
        db=defaultdict(lambda:float('inf'),{1:0,20:1})
        order=TotalOrder();order.rank(1);order.rank(20)
        order.hops[20]=1
        self.assertTrue(eligible_candidate(1,20,1,db,order))

if __name__=="__main__":
    unittest.main()
