import copy
from builtins import issubclass
from numpy import issubclass_


def to_arm(val):
    if isinstance(val, Strand):
        return Arm(val)

    assert isinstance(val, Arm), 'Input to to_arm must be "Arm" or "Strand"'
    return val
    

class _TakoType(type):
    """
    
    
    """
    def __new__(cls, name, bases, attr):
        
        __arms__ = {}
        if attr.get('__arms__') is not None:
            __arms__.update(attr['__arms__'])
        
        attr['__arms__'] = __arms__
        for k, arm in __arms__.items():
            __arms__[k] = to_arm(__arms__[k])
        
        return super().__new__(cls, name, bases, attr)

import inspect


class Tako(metaclass=_TakoType):
    """
    
    """
    class _TakoAttr(object):
        """
        Helper class used by tako to control the arms
        owner and parent should be contained in the neuron not the op
        
        """
        def __init__(self, arms, cls=None, owner=None, parent=None):
            """
            Need to replicate the neurons
            """
            self._arms = {}
            self._parent = parent
            self._owner = owner
            self._cls = cls
            for k, arm in arms.items():
                copied = arm.neuron_copy()
                self._arms[k] = copied
        
        def set_owner(self, owner):
            self._owner = owner
            for _, arm in self._arms:
                arm.strand().send_through(bot.call.set_owner(owner))
    
        def set_super(self, parent):
            """
            A 'SuperRef' will call this TakoAttr class when acting on it
            which will in turn call this TakoAttr if the attribute is an arm
            """
            for _, arm in self._arms:
                arm.strand().send_through(bot.call.set_parent(parent))
    
        def __getattribute__(self, k):
            return getattr(self._cls, k)

        def __setattribute__(self, k, v):
            return setattr(self._owner, k, v)
        
        def getarm(self, k):
            res = self._arms.get(k)
            if res is not None:
                return res
            if res is None and self._parent:
                return self._parent.getarm(k)
            raise AttributeError
    
        def setarm(self, k, v):
            arm = to_arm(v)
            self._arms[k] = arm
            if self._parent is not None:
                arm.strand().send_through(bot.call.set_parent(self._parent))
            if self._owner is not None:
                arm.strand().send_through(bot.call.set_owner(self._owner))
    
    def __new__(cls):
        instance = object.__new__(cls)
        cur = cls
        instance._arm_controller = cls._TakoAttr({}, instance, instance)
        prev_arm_controller = instance._arm_controller
        while True:
            cur_arm_controller = cls._TakoAttr(cur.__arms__, cur, instance)
            if prev_arm_controller is not None:
                prev_arm_controller.set_parent(cur_arm_controller)
            prev_arm_controller = cur_arm_controller

            super_ = cur.__base__ if issubclass(cur.__base__, Tako) else None
            if super_ is None or not issubclass(super_, Tako):
                break
            cur = super_

        return instance
    
    def __getattr__(self, k):
        return self._arm_controller.getarm(k)

    def __setattr__(self, k, v):
        # need to walk through this
        if type(v) is Strand or type(v) is Arm:
            self._arm_controller.setarm(k, v)
        else:
            self.__dict__[k] = v


"""
class _TakoType(type):
    # 
    
    encoder = arm(my.enc_layer1>>my.enc_layer2>>my.enc_layer3)
    decoder = arm(my.dec_layer1>>my.dec_layer2>>my.dec_layer3)
    autoencoder = arm(
        my.encoder>>my.decoder
    )
    oc.emit(my.x)>>
    
    def __new__(cls, <arguments>):
        print(cls)
        instance = super(Tako, cls).__new__(cls, *args, **kwargs)
        
        # create each tako arm <- find each arm first by looping through the dictionary
        
        # cls.__init__(instance, arg)
        return instance

class _ArmController(object)
    
    def __init__(self, parent, arms):
        self._parent = parent
        
        # defines the arms for this class
        # sets the super and sets the owner
        self._arms = arms

class Tako(metaclass=_TakoType):
    
    def __new__(cls):
        instance = object.__new__(cls)
        # defines all of the arms with _ArmController 
        # and adds them to instance
        
    def __init__(self):
        # don't really need init
        pass
        


"""

"""
x = arm.u << x << y << z
    arm.m >> nn.Linear(2, 2) >> addOne >> subTwo 


"""



class Op(object):
    
    def __init__(self):
        pass
    
    def __call__(self, x):
        raise NotImplementedError


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


