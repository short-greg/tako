import numpy as np
import math
import tako


class Accessor(object):
    '''
    Used to access data of a dataset
    Can use 'meta' accessors on top of the accessor to
    change the order/manner in which data is accessed
    '''
    def __init__(self, data=None):
        '''
        :param data: The data to be accessed (needs to accessible
        through __getitem__) (It might be good to add in
        a dictionary accessor as well)
        '''
        self._wrapped = False
        self._data = data

    def wrap(self, meta_acc):
        '''
        Wrap the accessor with a "meta_accessor"
        The meta accessor can randomize the order in which
        elements are retrieved, reverse the order
        (or potentially do transformations)
        :param meta_acc: MetaAccessor
        '''
        meta_acc.data = self._data
        self._data = meta_acc
    
    def to_iter(self):
        '''
        :return Iter: an iterator for the mmeta accessor
        '''
        return Iter(self._data)
    
    @property
    def data(self):
        '''
        Properties are used so that
        the setting/getting can be altered in
        child classes.
        '''
        return self._data
    
    @data.setter
    def data(self, data):
        self._data = data
    
    def __len__(self):
        return len(self._data) if self._data is not None else 0
    
    def __getitem__(self, idx):
        '''
        :param int idx: The index of the item to retrieve
        '''
        return self._data[idx]
    
    def __setitem__(self, idx, val):
        '''
        :param int idx: The index of the item to set
        :param val: The value to set it to
        '''
        
        self._data[idx] = val
    
    def __neuron__(self):
        return AccessorNeuron(self)

    def _spawn_data(self):
        if isinstance(self._data, MetaAccessor):  
            return self._data.spawn()
        return self._data
    
    def spawn(self):
        return Accessor(self._spawn_data())


class MetaAccessor(object):
    '''
    Wraps the MetaAccessor object into a neuron
    and outputs it when spawned
    '''
    def __init__(self, data=None):
        self._data = data
    
    def _spawn_data(self):
        if isinstance(self._data, MetaAccessor):
            return self._data.spawn()
        return self._data
    
    def spawn(self):
        raise NotImplementedError
    
    def __neuron__(self):
        return MetaAccessorNeuron()

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


class AccessorNeuron(tako.Neuron):
    '''
    Wraps the Accessor object into a neuron
    and outputs it when spawned
    '''
    
    def __init__(self, accessor):
        super().__init__()
        self._accessor = accessor
    
    def __call__(self, x, bot=None):
        accessor = self._accessor.spawn()
        accessor.data = x
        return accessor
    
    def spawn(self):
        return AccessorNeuron(self._accessor)


class MetaAccessorNeuron(tako.Neuron):
    '''
    Wraps the MetaAccessor object into a neuron
    and outputs it when spawned
    '''
    
    def __init__(self, accessor):
        super().__init__()
        self._meta_accessor = accessor
    
    def __call__(self, x, bot=None):
        accessor = self._meta_accessor.spawn()
        x.wrap(accessor)
        return x
    
    def spawn(self):
        return MetaAccessorNeuron(self._meta_accessor)


class Shuffle(MetaAccessor):
    '''
    Access the data in random order
    '''
    
    def __init__(self, data=None):
        super().__init__(data)
        self._order = None

    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, data):
        '''
        Sets the data and creates a new order to retrieve
        the data
        '''
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
        return Shuffle(self._spawn_data())


class Batch(MetaAccessor):
    '''
    Access the data in batches
    '''
    
    def __init__(self, data=None, size=1):
        super().__init__(data)
        self._size = size
    
    def __len__(self):
        return math.ceil(len(self._data) / self._size)
    
    def __getitem__(self, idx):
        return self._data[
            idx * self._size:min(
                len(self._data), (idx + 1) * self._size
            )]            
        #    return self._data:index(1, torch.range((index - 1) * self._size + 1, index * self._size):long())

    def __setitem__(self, idx, val):
        self._data[idx * self._size:min(len(self._data), (idx + 1) * self._size)] = val

    def spawn(self):
        return Batch(self._spawn_data(), self._size)


class Reverse(MetaAccessor):
    '''
    Access the data in reverse order
    '''
    
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

    def spawn(self):
        return Reverse(self._spawn_data())

    def __len__(self):
        return len(self._data)


class Iter(object):
    '''
    Iterator class to use for iterating over a dataset
    '''
    
    def __init__(self, data):
        '''
        Iterator class
        :param data: The data to iterate on (Can be an accessor or a sequential)
        '''
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
    '''
    Covert an accessor into an iterator
    '''
    
    def __init__(self):
        super().__init__()
    
    def __call__(self, x, wh=None):
        '''
        :param Accessor x: the accessor to iterate on
        :param bot: StoreBot
        '''
        return Iter(x)

    def spawn(self):
        return ToIter()


class Iterate(tako.Neuron):
    '''
    Neuron that iterates on the iterator 
    that is passed in until the iterator
    reaches the end
    '''
    
    AT_END = False, None
    
    def __call__(self, x, wh=None):
        '''
        :param Iter x: the iterator to iterate on
        :param bot: StoreBot
        '''
        if not x.at_end():
            result = x.get()
            x.adv()
        else:
            result = self.AT_END
        return True, result

    def spawn(self):
        return Iterate()
