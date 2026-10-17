"""Reference BatchPQ tests including strict BatchPrepend preconditions."""
import random
import unittest
from graphs.batch_pq_faithful_reference import BatchPQFaithfulReference

TOP=(float("inf"),)*3

class BatchPQFaithfulReferenceTests(unittest.TestCase):
    def test_sorted_batch_and_exclusive_limit(self):
        q=BatchPQFaithfulReference(2,TOP)
        for v,k in [(1,(3,0,1)),(2,(1,0,2)),(3,(2,0,3))]:
            q.insert(v,k)
        bound,batch=q.pull()
        self.assertEqual(batch,[2,3])
        self.assertEqual(bound,(3,0,1))
        self.assertEqual(q.pull(),(TOP,[1]))

    def test_decrease_key(self):
        q=BatchPQFaithfulReference(1,TOP)
        q.insert(1,(5,0,1));q.insert(2,(4,0,2))
        q.insert(1,(2,0,1))
        self.assertEqual(q.pull(),((4,0,2),[1]))

    def test_prepend_rejects_out_of_order(self):
        q=BatchPQFaithfulReference(2,TOP)
        q.insert(1,(4,0,1))
        with self.assertRaises(ValueError):
            q.batch_prepend([(2,(5,0,2))])
        self.assertEqual(q._key_val,{1:(4,0,1)})

    def test_legal_sequences(self):
        rng=random.Random(20261017)
        for M in (1,2,4,8):
            q=BatchPQFaithfulReference(M,TOP)
            data={}
            next_id=0
            for _ in range(200):
                action=rng.random()
                if action < .3 and data:
                    floor=min(k[0] for k in data.values())
                    if floor>0:
                        next_id+=1
                        val=(rng.randrange(floor),0,next_id)
                        q.batch_prepend([(next_id,val)])
                        data[next_id]=val
                elif action < .7:
                    next_id+=1
                    val=(rng.randrange(100,300),0,next_id)
                    q.insert(next_id,val)
                    data[next_id]=val
                else:
                    expected=sorted(data.items(),key=lambda p:p[1])
                    chosen=expected[:M]
                    limit=expected[len(chosen)][1] if len(expected)>len(chosen) else TOP
                    self.assertEqual(q.pull(),(limit,[v for v,_ in chosen]))
                    for v,_ in chosen:del data[v]
                self.assertEqual(q._key_val,data)

if __name__=="__main__":
    unittest.main()
