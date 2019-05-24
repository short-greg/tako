from flow import Stimulator, Neuron
from __init__ import Op

"""
import copy
class _TakoMeta(object): # type): # type):
    
    # 1. needs to create the __arms__
    
    # auto_encode = In_ >> my.encoder >> my.decoder
    
    
    # def ____(cls, class_name: str, class_bases: tuple, class_attrs: dict):
    def __new__(cls): # , class_name: str, class_bases: tuple, class_attrs: dict):
        cls = object.__new__(cls)
        __arms__ = cls.__arms__ if hasattr(cls, '__arms__') else {}
        for k, v in cls.__dict__.items():
            if isinstance(v, Strand):
                __arms__[k] = Arm(v)
            if isinstance(v, Arm):
                __arms__[k] = v

        cls.__arms__ = __arms__
        
        return cls

        # class_attrs[k] = float(attr)
        # cls = type.__new__(cls, class_name, class_bases, class_attrs)

class Tako(metaclass=_TakoMeta):
    
    def __init__(self):
        pass
        # Need to loop over the bases and generate the arm accessors
"""

class DeclarationStimulator(Stimulator):
    
    def __init__(self, op, fix_op=True):
        self._fix_op = fix_op
        self.op = op

    def __call__(self, x, bot):
        if self._fix_op:
            self.op = self.op.define(x)
            self.__call__ = super().__call__
        return self.op(x)


class Declaration(Neuron):
    
    def __init__(self, module_cls, fix_op=True, args, kwargs):
        self.module_cls = module_cls
        self.op = None
        self._args = args
        self._kwargs = kwargs
        self._fix_op = fix_op
        
    def define(self, x=None):
        """
        
        """
        # need to have code to define a module in
        # here
        return self.module_cls(*self._args, **self._kwargs)
    
    def _replace(self, replace_with):
        self.incoming.replace_outgoing(self, replace_with)
        for outgoing in self.outgoing:
            outgoing.incoming = self

    def __call__(self, x):
        op = self.define(x)
        if self._fix_op:
            neuron = to_neuron(op)
            self._replace(neuron)
            
        return op(x)
    
    def __neuron__(self):
        return Neuron(self, DeclarationStimulator())


@classmethod
def declaration(cls):
    return Declaration(cls)
