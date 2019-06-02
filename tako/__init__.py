from tako import bot

######################################################
# Core Neuron Modules
# 
# A flow is the core component of the information
# network
#
######################################################

class Neuron(object):
    """
    The base flow class
    
    """
    def __init__(self):
        self.incoming = None
        self.outgoing = None
    
    @property
    def key(self):
        return hash(self)
    
    def visit(self, bot):
        return bot(self)
    
    def spawn(self):
        return Neuron()
    
    def bot_forward(self, bot):
        if self.visit(bot) and self.outgoing is not None:
            self.outgoing.bot_forward(bot)
    
    def forward(self, x, bot=None):
        x = self(x, bot)
        if self.outgoing is not None:
            return self.outgoing.forward(x, bot)
        return x

    def connect(self, other):
        other._connect_incoming(self)
        self._connect_outgoing(other)
    
    def _connect_incoming(self, other):
        assert self.incoming is None, 'There can only be one incoming flow for a flow'
        self.incoming = other
        
    def _connect_outgoing(self, other):
        assert self.outgoing is None, 'There can only be one incoming flow for a flow'
        self.outgoing = other
    
    # for bot
    # use hash(self) <- get the hash for the flow and 
    # pass it to the bot.. 
    # or just send the bot self... not sure which to do yet

    def __call__(self, x, bot):
        raise NotImplementedError


class _In(Neuron):
    """
    Used for convenience to create a strand where the following objects are
    'ops' so that those ops will properly be converted to neurons
    
    It should come at the start of a strand (especially those strands used
    within neurons that control flow.) The reason for this is because of the
    "declaration" objects used to declare a new class
    """
    def __init__(self):
        super().__init__()
    
    def spawn(self):
        return _In()
    
    def _connect_incoming(self, other):
        raise AttributeError('An In flow cannot have any incoming neurons')
    
    # def probe(self, bot):
    #    return self.x
    
    def __getitem__(self, key):
        return to_neuron(Sub(key))

    def __rshift__(self, other):
        return Strand([self, other])
    
    def __call__(self, x, bot=None):
        return x


class _Out(Neuron):
    """
    Used for convenience to create a strand where the following objects are
    'ops' so that those ops will properly be converted to neurons
    """
    def __init__(self):
        super().__init__()
    
    def spawn(self):
        return _Out()
    
    def _connect_outgoing(self, other):
        raise AttributeError('An In flow cannot have any incoming neurons')
    
    def bot_forward(self, bot):
        self.visit(bot)

    def __getitem__(self, key):
        return to_neuron(Sub(key))

    def __rshift__(self, other):
        raise AttributeError('An "Out_" flow cannot output to another flow. ')
    
    def __call__(self, x, bot=None):
        return x


class _Nil(_In):
    """
    Primarily a convenience for creating 'strands' with Emit Neurons
    This is used as the starting flow for the case where there
    is no input into the network
    """
    def __init__(self):
        super().__init__()
    
    def spawn(self):
        return _Nil()
    
    def _connect_incoming(self, other):
        raise AttributeError('A "Nil" flow cannot have any incoming neurons')
    
    """
    def inform(self, x=None, bot=None):
        assert x is None, 'Cannot inform nil Neuron'
        return super().inform(x, bot)
    """

    def __getitem__(self, key):
        raise NotImplementedError

    def __rshift__(self, other):
        return Strand([self, other])
    
    def __call__(self, x, bot=None):
        assert x is None, 'The input to a Nil flow must be None'
        return x
    
class _InCreator(object):
    
    def __rshift__(self, other):
        return _In() >> other


in_ = _InCreator()


class _OutCreator(object):
    
    def __rshift__(self, other):
        return _Out() >> other

out_ = _OutCreator()


class _NilCreator(object):
    
    def __rshift__(self, other):
        return _Nil() >> other


nil_ = _NilCreator()


class Stimulator(object):
    """
    Stimulator is used to stimulate a particular operation
    in the op nerve
    TODO: "I am not sure if it is still needed"
    
    """
    def __init__(self, op):
        self.x = None
        self.op = op
    
    def __call__(self, x, bot=None):
        return self.op(x)


class UnpackStimulator(Stimulator):
    """
    Stimulator is used to stimulate a particular operation
    in the op nerve
    TODO: "I am not sure if it is still needed"
    
    """
    def __call__(self, x, bot=None):
        return self.op(*x)


class Sub(Neuron):
    
    def __init__(self, index):
        super().__init__()
        self.index = index
    
    def __call__(self, x, bot=None):
        return x[self.index]
    
    def spawn(self):
        return Sub(self.index)


class OpNeuron(Neuron):
    """
    Op flow calls an particular operation
    """
    def __init__(self, op, stimulator_cls=Stimulator):
        super().__init__()
        self._op = op
        self._stimulator_cls = stimulator_cls
        self.stimulator = stimulator_cls(op)
    
    def spawn(self):
        return OpNeuron(self._op, self._stimulator_cls)
    
    def __call__(self, x, bot=None):
        return self.stimulator(x)


class Noop(Neuron):
    """
    Noop neurons do not perform any operation
    """
    def spawn(self):
        return Noop()
    
    def __call__(self, x, bot=None):
        return x

# TODO: Refactor.. duplicating Stem
def update_arg(arg, *args, **kwargs):
    if isinstance(arg, Arg):
        return arg.update(*args, **kwargs)
    else:
        return arg


class Arg(object):
    """
    Args are used in stems to provide variable
    rather than constant arguments to the
    neurons created by the stem
    """
    def __init__(self, key):
        self._key = key

    @property
    def key(self):
        return self._key
    
    def update(self, *args, **kwargs):
        if type(self._key) == int:
            return args[self._key]
        else:
            return kwargs[self._key]


class _Arg(object):
    """
    
    
    """
    def __getattribute__(self, key):
        return Arg(key)

    def __getitem__(self, key):
        return Arg(key)


arg = _Arg()

# TODO: This is not right right now
# TODO: This is not right right now
class Declaration(Neuron):
    """    
    Declaration will define a neural network
    
    """
    def __init__(self, module_cls, args=None, kwargs=None, dynamic=False):
        super().__init__()
        args = args or []
        kwargs = kwargs or {}
        self.defined = None
        self.module_cls = module_cls
        self._args = args
        self._kwargs = kwargs
        self._dynamic = dynamic

    def update_args(self, args, kwargs):
        self._kwargs = {k: update_arg(arg, *args, **kwargs) for k, arg in self._kwargs.items()}
        self._args = [update_arg(arg, *args, **kwargs) for arg in self._args]
        
    def define(self, x=None):
        """
        
        """
        # need to have code to define a module in
        # here
        defined = to_neuron(self.module_cls(*self._args, **self._kwargs))
        self.defined = defined
        return defined
    
    def _replace(self, replace_with):
        if self.incoming:
            self.incoming.outgoing = replace_with
            replace_with.incoming = self.incoming
        if self.outgoing:
            self.outgoing.incoming = replace_with
            replace_with.outgoing = self.outgoing
        self.incoming = None
        self.outgoing = None

    def __call__(self, x, bot=None):
        if not self._dynamic and not self.defined:
            neuron = self.define(x)
            self._replace(neuron)
            return neuron(x, bot)
        elif not self._dynamic:
            return self.defined(x, bot)
        else:
            return self.define(x)(x, bot)


def decl(cls, *args, **kwargs):
    return Declaration(cls, args, kwargs)


@classmethod
def _cls_decl(cls, *args, **kwargs):
    return Declaration(cls, args, kwargs)

Neuron.d = _cls_decl


class Stem(object):
    """
    Stems provide templates for creating arms
    """
    def __init__(self, cls, *args, **kwargs):
        self._cls = cls
        self._args = args
        self._kwargs = kwargs
    
    def __call__(self, *args, **kwargs):
        updated_kwargs = {k: self.update_arg(arg, kwargs) for k, arg in self._kwargs.items()}
        updated_args = [update_arg(arg, *args, **kwargs) for arg in self._args]

        # need to use a bot to update it for 
        bot.call.update_arg(
            cond=lambda x: isinstance(x, Declaration),
            args=(args, kwargs)
        )
        return self._cls(*updated_args, **updated_kwargs)


class Emit(Neuron):
    """
    Emit outputs the value that has been passed in
    It cannot have an incoming nerve as 
    """
    def __init__(self, to_emit):
        super().__init__()
        self._to_emit = to_emit
        """
        if isinstance(to_emit, Ref):
            self.__call__ = self._evaluate_ref
        else:
            self.__call__ = self._evaluate
        """

    def spawn(self):
        return Emit(self._to_emit)

    def inform(self, x=None, bot=None):
        assert x is None, (
            'Cannot inform an Emit flow with a value ' +
            '(Must pass not value or None)'
        )
        return super().inform(x, bot)

    """
    def _evaluate(self, x):
        assert x is None, 'Emit Neurons must not take an input.'
        return self._to_emit
    
    def _evaluate_ref(self, x):
        assert x is None, 'Emit Neurons must not take an input.'
        return self._to_emit()
    """

    def __call__(self, x=None, bot=None):
        assert x is None, 'Emit Neurons must not take an input.'
        return self._to_emit


def to_neuron(x):
    """
    
    """
    if isinstance(x, Neuron):
        """
        it is already a flow so nothing needs to be done
        """
        return x
    if hasattr(x, '__neuron__'):
        """
        There is a dedicated method to convert the
        object intoa flow
        """
        return x.__neuron__()

    if x is None:
        """
        
        """
        return Noop()
    
    # The default is to use an OpNeuron
    return OpNeuron(x)


######################################################
# Strand and Arm are the core classes used to control 
# flow. 
# Arm encapsulates Strand into a flow
# so that Arm can then be connected to other neurons
#
######################################################


class Strand(object):
    """
    
    """
    def __init__(self, neurons):
        assert len(neurons) > 0, 'There must be more than one operation'
        self.lhs, self.rhs = self._connect_ops(neurons)

    def _connect_ops(self, neurons):
        """
        Links a list of ops together in order to form a 'strand'
        
        """
        lhs = None
        rhs = None
        prev = None
        for neuron in neurons:
            cur = to_neuron(neuron)
            if lhs is None:
                lhs = cur
                rhs = cur
            else:
                rhs = cur
                prev.connect(cur)
            prev = cur
        return lhs, rhs
    
    def __getitem__(self, index):
        i = 0
        cur = self.lhs
        while cur is not self.rhs:
            if i == index:
                return cur
            cur = cur.outgoing
            i += 1

        if i == index:
            return cur
        raise IndexError
    
    def append(self, mod):
        rhs = to_neuron(mod)
        self.rhs.connect(rhs)
        self.rhs = rhs
    
    def prepend(self, mod):
        lhs = to_neuron(mod)
        lhs.connect(self.lhs)
        self.lhs = lhs

    def encapsulate(self, left_nil=False):
        if not isinstance(self.rhs, _Out):
            self.append(_Out())
        if not isinstance(self.lhs, _In):
            if not left_nil:
                self.prepend(_In())
            else:
                self.prepend(_Nil())
        
        return self

    def arm(self):
        return Arm(self)

    def bot_forward(self, bot):
        self.lhs.bot_forward(bot)
    
    def spawn(self):
        cur = self.lhs
        ops = []
        while cur is not self.rhs:
            ops.append(cur.spawn())
            cur = cur.outgoing
        ops.append(cur.spawn())
        return Strand(ops)

    def __call__(self, x=None, bot=None):
        return self.lhs.forward(x, bot)
        # self.lhs.inform(x, bot)
        # return self.rhs.probe()
    
    def __rshift__(self, other):
        """
        
        # Do I just want to call append????
        """
        self.append(other)
        return self


Strand.__neuron__ = Strand.arm
        

def neuron_rshift(self, other):
    return Strand([self, other])

Neuron.__rshift__ = neuron_rshift


class Arm(Neuron):
    """
    Arms wrap strands so that they can be
    like neurons
    """
    def __init__(self, strand):
        super().__init__()
        self.strand = strand.encapsulate()

    def bot_forward(self, bot):
        self.strand.bot_forward(bot)

    def __call__(self, x, bot=None):
        return self.strand(x)

    def spawn(self):
        # Need to create this method
        return Arm(self.strand.spawn())
    
    @staticmethod
    def from_neuron(neuron):
        return Arm(Strand([neuron]))


######################################################
# 
# 
#
######################################################

class _TakoType(type):
    """
    
    
    """
    def __new__(cls, name, bases, attr):
        
        __arms__ = {}
        for k, v in attr.items():
            if isinstance(v, Strand) or isinstance(v, Arm):
                __arms__[k] = v

        if attr.get('__arms__') is not None:
            __arms__.update(attr['__arms__'])
        
        attr['__arms__'] = __arms__
        for k, arm in __arms__.items():
            __arms__[k] = to_arm(__arms__[k])

        return super().__new__(cls, name, bases, attr)

import inspect


def to_arm(val):
    if isinstance(val, Strand):
        return Arm(val)

    assert isinstance(val, Arm), 'Input to to_arm must be "Arm" or "Strand"'
    return val


def is_arm(v):
    return isinstance(v, Strand) or isinstance(v, Arm)


class Tako(object, metaclass=_TakoType):
    """
    
    """
    class _TakoAttr(object):
        """
        Helper class used by tako__ to control the arms
        owner and parent should be contained in the flow not the op
        
        """
        def __init__(
            self, arms, cls=None, owner=None, 
            parent=None
        ):
            """
            Need to replicate the neurons
            """
            self._arms = {}
            self._parent = parent
            self._owner = owner
            self._cls = cls
            for k, arm in arms.items():
                copied = arm.spawn()
                self._arms[k] = copied
        
        def set_owner(self, owner):
            self._owner = owner
            for _, arm in self._arms.items():
                arm.bot_forward(bot.call.set_owner(owner))
    
        def set_parent(self, parent):
            """
            A 'SuperRef' will call this TakoAttr class when acting on it
            which will in turn call this TakoAttr if the attribute is an arm
            """
            self._parent = parent
            for _, arm in self._arms.items():
                arm.bot_forward(bot.call.set_parent(parent))
    
        def __getattr__(self, k):
            return getattr(self._cls, k)

        # def __setattr__(self, k, v):
        #    return setattr(self._owner, k, v)
        
        def getarm(self, k):
            res = self._arms.get(k)
            if res is not None:
                return res
            if res is None and self._parent:
                return self._parent.getarm(k)
            raise AttributeError('Attribute {} does not exist.'.format(k))
    
        def setarm(self, k, v):
            arm = to_arm(v)
            self._arms[k] = arm
            if self._parent is not None:
                arm.bot_forward(bot.call.set_parent(self._parent))
            if self._owner is not None:
                arm.bot_forward(bot.call.set_owner(self._owner))
    
    def __new__(cls):
        instance = object.__new__(cls)
        cur = cls
        # The problem is in here
        instance.__armc__ = Tako._TakoAttr({}, instance, instance)
        prev_arm_controller = instance.__armc__
        while True:
            cur_arm_controller = cls._TakoAttr(cur.__arms__, cur, instance)
            prev_arm_controller.set_parent(cur_arm_controller)
            prev_arm_controller = cur_arm_controller

            cur = cur.__base__
            if not (issubclass(cur, Tako) or cur == Tako):
                break

        return instance
    
    def __init__(self):
        pass

    def __getattribute__(self, k):
        try:
            v = object.__getattribute__(self, k)
            if is_arm(v):
                return object.__getattribute__(self, '__armc__').getarm(k)
            return v
        except:
            # Still need to check the class
            pass
        
        cls = object.__getattribute__(self, '__class__')
        if hasattr(cls, k):
            v = getattr(cls, k)
            if is_arm(v):
                return object.__getattribute__(
                    self, '__armc__'
                ).getarm(k)
            return v
        raise AttributeError('Attribute {} not defined for Tako {}'.format(k, self))

    def __setattribute__(self, k, v):
        # need to walk through this
        if is_arm(v):
            self.__armc__.setarm(k, v)
        object.__setattribute__(self, k, v)


if __name__ == '__main__':
    neuron = Neuron()
    # HOw to deal with this abomination??? need to check that self
    strand = neuron>>neuron
    
    strand = (Neuron() >> Neuron() >> Neuron()).encapsulate()
    
    class T(object):
        x = 1
        def __getattribute__(self, k):
            return object.__getattribute__(self, k)
    
    # t = T() 
    # print(t.x)
    
    def t(x):
        return x + 1
    
    class X(Tako):
        strand = in_ >> t
        
    class YType(type):
        
        def __new__(cls, name, bases, attr):
            return super().__new__(
                cls, name, bases, attr
            )

    print(X().strand(1))
    
    """
    # getting infinite recursion here. Need to check this out
    # Tako is resulting in a lot of recursion
    # print(X().strand)
    # print(type(strand.rhs))
    """
