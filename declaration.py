from flow import Stimulator, Neuron
import __init__ as tako

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
"""

class Declaration(Neuron):
    """
    
    
    Declaration will define a neural network
    
    """
    
    def __init__(self, module_cls, fix=False, *args, **kwargs):
        self.module_cls = module_cls
        self._args = args
        self._kwargs = kwargs
        self._fix = fix
        
    # TODO: Refactor.. duplicating Stem
    @staticmethod
    def update_arg(arg, update_with):
        if isinstance(arg, Arg):
            return update_with[arg.key]
        else:
            return arg

    def update_args(self, args, kwargs):
        self._kwargs = {k: self.update_arg(arg, kwargs) for k, arg in self._kwargs.items()}
        self._args = [self.update_arg(arg, args) for arg in self._args]
        
    def define(self, x=None):
        """
        
        """
        # need to have code to define a module in
        # here
        return tako.to_neuron(self.module_cls(*self._args, **self._kwargs))
    
    def _replace(self, replace_with):
        self.incoming.outgoing = replace_with
        self.outgoing.incoming = replace_with
        replace_with.incoming = self.incoming
        replace_with.outgoing = self.outgoing
        self.incoming = None
        self.outgoing = None
        

    def __exec__(self, x):
        neuron = self.define(x)
        if self._fix:
            self._replace(neuron)
            
        return neuron(x)


@classmethod
def decl(cls, *args, **kwargs):
    return Declaration(cls, *args, **kwargs)
