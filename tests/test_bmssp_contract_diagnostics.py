import unittest
from collections import defaultdict
from graphs.batch_pq import TotalOrder
from graphs.bmssp_contract_diagnostics import (
    BMSSPContractViolation, check_child_entry, check_base_case_result)

class BMSSPContractDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.order=TotalOrder()
        self.labels=defaultdict(lambda:float('inf'),{1:1,20:1,27:1})
        for v in (1,20,27):
            self.order.rank(v)
        self.order.hops[1]=5
        self.order.hops[20]=3
        self.order.hops[27]=3

    def test_minimal_nonprogress_is_detected(self):
        with self.assertRaisesRegex(BMSSPContractViolation,"nonprogress"):
            check_base_case_result(
                seed=1,bound=self.order.TOP,returned_bound=self.order.key(1,self.labels),
                completed={20,27},labels=self.labels,order=self.order)

    def test_valid_base_return(self):
        check_base_case_result(
            seed=1,bound=self.order.TOP,returned_bound=self.order.TOP,
            completed={1,20,27},labels=self.labels,order=self.order)

    def test_child_bound_rejected(self):
        with self.assertRaisesRegex(BMSSPContractViolation,"exceeds parent"):
            check_child_entry(level=0,bound=(4,0,1),sources={1},
                labels=self.labels,order=self.order,parent_bound=(3,0,1))

    def test_frontier_key_rejected(self):
        with self.assertRaisesRegex(BMSSPContractViolation,"strict bound"):
            check_child_entry(level=0,bound=(1,4,9),sources={1},
                labels=self.labels,order=self.order)

if __name__=="__main__":
    unittest.main()
