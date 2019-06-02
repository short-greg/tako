import copy
from builtins import issubclass
from numpy import issubclass_







"""
x = arm.u << x << y << z
    arm.m >> nn.Linear(2, 2) >> addOne >> subTwo 


"""




def iterator_exception(self):
    raise Exception('Cannot iterate over a module.')


# Strand.__getitem__ = get_item
Neuron.__getitem__ = get_item
Neuron.iterator = iterator_exception










class Const(Op):
    def __init__(self, val):
        self._val = val

    def __call__(self, x=None):
        assert x is None, 'Op Const must not take an input value'
        return



"""
class _Out(Nerve):
    # Apply operations onto the output of a nerve
    
    def probe(self):
        raise NotImplementedError('The class _in does not implement probe')
    
    def __rshift__(self):
        pass

out_ = _Out()
"""



"""
class Emit(nn.Module):
    def __init__(self, to_emit):
        self._to_emit = to_emit
        if isinstance(self._to_emit, RefBase):
            self.emit = self._emit_ref
        else:
            self.emit = self._emit_val

    def _emit_ref(self, x):
        return self._to_emit(x)
        
    def _emit_val(self, x):
        return self._to_emit
        
    def forward(self, x=None):
        assert x is None, "Input to forward must be undefined"
        return self.emit(x)
"""


