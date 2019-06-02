import numpy as np
import math
import __init__ as tako



class Accessor(object):
    
    def __init__(self, data=None):
        self._data = data

    def wrap(self, meta_iter):
        meta_iter.data = self._data
        self._data = meta_iter
    
    def to_iter(self):
        return Iter(self._data)
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, data):
        self._data = data
    
    def __len__(self):
        return len(self._data) if self._data is not None else 0
    
    def __getitem__(self, idx):
        return self._data[idx]
    
    def __setitem__(self, idx, val):
        self._data[idx] = val
    
    def __neuron__(self):
        return AccessorNeuron(self)
    
    def spawn(self):
        # TODO: what if data is meta
        # don't worry about it
        return Accessor(self._data)


class AccessorNeuron(tako.Neuron):
    
    def __init__(self, accessor, spawn_with_in=True):
        super().__init__()
        self._accessor = accessor
        self._spawn_with_in = spawn_with_in
    
    def __call__(self, x, bot=None):
        accessor = self._accessor.spawn()
        accessor.data = x
        return accessor
    
    def spawn(self):
        return AccessorNeuron(self._accessor)


class MetaAccessor(object):
    def __init__(self, data=None):
        self._data = data
    
    def spawn(self):
        return MetaAccessor(self._data)

    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, data):
        self._data = data
    
    def __getitem__(self, idx):
        raise NotImplementedError
    
    def __setitem__(self, idx, val):
        raise NotImplementedError
        

class Shuffle(MetaAccessor):
    
    def __init__(self, data=None):
        super().__init__(data)
        self._order = None

    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, data):
        self._data = data
        if data is not None:
            self._order = np.random.permutation(len(data))
        else:
            self._order = []

    def __len__(self):
        return len(self._data)
    
    def __getitem__(self, idx):
        return self._data[self._order[idx]]

    def __setitem__(self, idx, val):
        self._data[self._order[idx]] = val

    def spawn(self):
        return Shuffle(self._data)


class Batch(MetaAccessor):
    
    def __init__(self, data=None, size=1):
        super().__init__(data)
        self._size = size
    
    def __len__(self):
        return math.ceil(len(self._data) / self._size)
    
    def __getitem__(self, idx):
        return self._data[idx * self._size:min(len(self._data), (idx + 1) * self._size)]            
        #    return self._data:index(1, torch.range((index - 1) * self._size + 1, index * self._size):long())

    def __setitem__(self, idx, val):
        self._data[idx * self._size:min(len(self._data), (idx + 1) * self._size)] = val

    def spawn(self):
        return Batch(self._data, self._size)


class Reverse(MetaAccessor):
    
    def __getitem__(self, idx):
        size = len(self._data)
        pos = size - idx
        if pos > 0:
            return self._data[len(self) - idx - 1]
        
        raise IndexError

    def __setitem__(self, idx, val):
        size = len(self._data)
        pos = size - idx
        if pos > 0:
            self._data[len(self) - idx - 1] = val

        raise IndexError

    def __len__(self):
        return len(self._data)


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
    
    def adv(self):
        if not self.at_end():
            self._idx += 1
    
    def spawn(self):
        return Iter(self._data)


class ToIter(tako.Neuron):
    
    def __init__(self):
        super().__init__()
    
    def __call__(self, x, bot=None):
        return Iter(x)

    def spawn(self):
        return ToIter()


class Iterate(tako.Neuron):
    
    AT_END = tuple()
    
    def __call__(self, x, bot=None):
        if not x.at_end():
            result = x.get()
            x.adv()
        else:
            result = self.AT_END
        return result

    def spawn(self):
        return Iterate()
