"""Differential test for experimental heap queue vs reference queue."""
import math
import random
import unittest
from graphs.batch_pq_faithful_reference import BatchPQFaithfulReference
from graphs.batch_pq_incremental import BatchPQIncremental

class IncrementalQueueTest(unittest.TestCase):
    def test_legal_sequences(self):
        r=random.Random(88228)
        for trial in range(100):
            M=r.choice([1,2,4,8])
            qs=[BatchPQFaithfulReference(M,(math.inf,)*3),
                BatchPQIncremental(M,(math.inf,)*3)]
            next_id=0
            for step in range(300):
                a=r.random()
                active=qs[0]._key_val
                if a<.25 and active:
                    floor=min(x[0] for x in active.values())
                    if floor>0:
                        next_id+=1
                        items=[(next_id,(r.randrange(floor),0,next_id))]
                        for q in qs:q.batch_prepend(items)
                elif a<.65:
                    if active and r.random()<.3:
                        v=r.choice(list(active))
                        new=(max(0,active[v][0]-r.randint(1,15)),0,v)
                    else:
                        next_id+=1
                        v=next_id
                        new=(r.randrange(50,500),0,v)
                    for q in qs:q.insert(v,new)
                else:
                    self.assertEqual(qs[0].pull(),qs[1].pull(),
                                     (trial,step))
                self.assertEqual(qs[0]._key_val,qs[1]._key_val,
                                 (trial,step))
if __name__=="__main__":
    unittest.main()
