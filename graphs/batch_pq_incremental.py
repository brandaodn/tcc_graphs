"""Experimental incremental heap-backed bounded queue. NOT Lemma 3.3 complexity."""
import heapq
import itertools

class BatchPQIncremental:
    def __init__(self,M,B):
        if M<1:raise ValueError("M must be >=1")
        self.M,self.B=M,B
        self._key_val={}
        self._heap=[]
        self._seq=itertools.count()
    def insert(self,vertex,key):
        if key>=self.B:return
        old=self._key_val.get(vertex)
        if old is None or key<old:
            self._key_val[vertex]=key
            heapq.heappush(self._heap,(key,next(self._seq),vertex))
        if len(self._heap)>max(128,4*len(self._key_val)):
            self._heap=[item for item in self._heap if self._key_val.get(item[2])==item[0]]
            heapq.heapify(self._heap)
    def batch_prepend(self,pairs):
        items=list(pairs)
        if self._key_val and items:
            smallest=min(self._key_val.values())
            if any(key>=smallest for _,key in items):
                raise ValueError("BatchPrepend requires keys below current minimum")
        for vertex,key in items:self.insert(vertex,key)
    def _trim(self):
        while self._heap and self._key_val.get(self._heap[0][2])!=self._heap[0][0]:
            heapq.heappop(self._heap)
    def pull(self):
        chosen=[]
        while len(chosen)<self.M:
            self._trim()
            if not self._heap:break
            key,_,vertex=heapq.heappop(self._heap)
            if self._key_val.get(vertex)!=key:continue
            del self._key_val[vertex]
            chosen.append(vertex)
        self._trim()
        return (self._heap[0][0] if self._heap else self.B),chosen
    def is_empty(self):return not self._key_val
