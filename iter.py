import numpy as np
import math
import __init__ as tako



class Accessor(object):
    
    def __init__(self, data):
        self._data = data
    
    def wrap(self, meta_iter):
        meta_iter.set_data(self._data)
        self._data = meta_iter
    
    def to_iter(self):
        return Iter(self._data)
    
    def __len__(self):
        return len(self._data)


class MetaAccessor(object):
    def __init__(self, data):
        self._data = None
        self.set_data(data)
        
    def set_data(self, data):
        self._data = data
        

class Shuffle(MetaAccessor):
    
    def __init__(self, data):
        self._order = None
        super().set_data(data)
    
    def set_data(self, data=None):
        self._data = data
        if data is not None:
            self._order = np.random.permutation(len(data))
        else:
            self._order = []
    
    def __len__(self):
        return len(self._data)
    
    def __getitem__(self, idx):
        return self._data[self._order[idx]]


class Batch(MetaAccessor):
    
    def __init__(self, data, size=1):
        self._size = size
        super().__init__(data)
    
    def __len__(self):
        return math.floor(self._data.size(0) / self._size)
    
    def __getitem__(self, idx):
        return self._data.index(
        #    return self._data:index(1, torch.range((index - 1) * self._size + 1, index * self._size):long())

        )
    

class Reverse(MetaAccessor):
    
    def __getitem__(self, idx):
        size = len(self._data)
        pos = size - idx
        if pos > 0:
            return self._data[self._size - idx - 1]
        
        raise IndexError


class Iter(object):
    
    def __init__(self, data):
        self._data = data
        self._idx = 0
        self._end = len(data)
    
    def get(self):
        if not self.at_end():
            return self._data[self._idx]
        # TODO: Raise error?
    
    def set(self, value):
        if not self.at_end():
            self._data[self._idx] = value
    
    def at_end(self):
        return self._idx == self._end


class ToIter(tako.Neuron):
    
    def __init__(self):
        super().__init__()
    
    def __exec__(self, x):
        return Iter(x)


class Iterate(tako.Neuron):
    
    AT_END = tuple()
    
    def __exec__(self, x):
        if not x.at_end():
            result = x.get()
            x.adv()
        else:
            result = self.AT_END
        return result
