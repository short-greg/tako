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



class Adapter(Op):
    
    def __init__(self, to_inform, to_probe):
        self._to_inform = nerve(to_inform)
        self._to_probe = nerve(to_probe)
        if type(to_probe) == 'list':
            self._probe = self._probe_list
        else:
            self._probe = self._probe_value
        
        if type(to_inform) == 'list':
            self._inform = self._inform_list
        else:
            self._inform = self._inform_value
    
    def _inform(self):
        raise NotImplementedError('Inform method must be overwritten on construction.')
    
    def _probe(self):
        raise NotImplementedError('Probe method must be overwritten on construction.')
    
    def _inform_value(self, x):
        self._to_inform(x)
    
    def _inform_list(self, x):
        for to_inform, item in zip(self._to_inform, x):
            to_inform(item)
    
    def _probe_list(self):
        result = []
        for to_probe in self._to_probe:
            result.append(to_probe())
        return result

    def _probe_value(self):
        return self._to_probe()


class Noop(Op):
    def __call__(self, x):
        return x


class ToNone(Op):
    def __call__(self, x):
        return None


class Const(Op):
    def __init__(self, val):
        self._val = val

    def __call__(self, x=None):
        assert x is None, 'Op Const must not take an input value'
        return

class Arg(object):
    def __init__(self, key):
        self._key = key

    @property
    def key(self):
        return self._key


class _Arg(object):
    
    def __getattribute__(self, key):
        return Arg(key)

    def __getitem__(self, key):
        return Arg(key)


arg = _Arg()

# TODO: This is not right right now


class Stem(object):
    
    def __init__(self, cls, *args, **kwargs):
        self._cls = cls
        self._args = args
        self._kwargs = kwargs
    
    @staticmethod
    def _update_arg(arg, update_with):
        if isinstance(arg, Arg):
            return update_with[arg.key]
        else:
            return arg
    
    def __call__(self, *args, **kwargs):
        updated_kwargs = {k: self._update_arg(arg, kwargs) for k, arg in self._kwargs.items()}
        updated_args = [self._update_arg(arg, args) for arg in self._args]
        return self._cls(*updated_args, **updated_kwargs)


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


