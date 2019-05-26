import bot

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
    
    def visit(self, bot):
        return bot(self)
    
    def spawn(self):
        return Neuron()
    
    def bot_forward(self, bot):
        if self.visit(bot) and self.outgoing is not None:
            self.outgoing.bot_forward(bot)
    
    def bot_backward(self, bot):
        if self.visit(bot) and self.incoming is not None:
            self.incoming.bot_backward(bot)
    
    def forward(self, x, bot):
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
    
    # def probe(self, bot):
    #    raise NotImplementedError
    
    def inform(self, x, bot=None):
        bot = bot or bot.Warehouse()
        bot.inform(hash(self), x)
        return bot
    
    def __exec__(self, x):
        raise NotImplementedError
    
    def __call__(self, x, bot=None):
        if bot is not None:
            x = bot.probe(hash(self))
        return self.__exec__(x)


class In_(Neuron):
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
        return In_()
    
    def _connect_incoming(self, other):
        raise AttributeError('An In flow cannot have any incoming neurons')
    
    def bot_backward(self, bot):
        self.visit(bot)
    
    # def probe(self, bot):
    #    return self.x
    
    def __getitem__(self, key):
        return to_neuron(Sub(key))

    def __rshift__(self, other):
        return Strand([self, other])
    
    def __exec__(self, x):
        return x


class Out_(Neuron):
    """
    Used for convenience to create a strand where the following objects are
    'ops' so that those ops will properly be converted to neurons
    """
    def __init__(self):
        super().__init__()
    
    def spawn(self):
        return Out_()
    
    def _connect_outgoing(self, other):
        raise AttributeError('An In flow cannot have any incoming neurons')
    
    def bot_forward(self, bot):
        self.visit(bot)

    def __getitem__(self, key):
        return to_neuron(Sub(key))

    def __rshift__(self, other):
        raise AttributeError('An "Out_" flow cannot output to another flow. ')
    
    def __exec__(self, x):
        return x

class Nil_(In_):
    """
    Primarily a convenience for creating 'strands' with Emit Neurons
    This is used as the starting flow for the case where there
    is no input into the network
    """
    def __init__(self):
        super().__init__()
    
    def spawn(self):
        return Nil_()
    
    def _connect_incoming(self, other):
        raise AttributeError('A "Nil" flow cannot have any incoming neurons')
    
    def inform(self, x=None, bot=None):
        assert x is None, 'Cannot inform nil Neuron'
        return super().inform(x, bot)

    def __getitem__(self, key):
        raise NotImplementedError

    def __rshift__(self, other):
        return Strand([self, other])
    
    def __exec__(self, x):
        assert x is None, 'The input to a Nil flow must be None'
        return x


class Stimulator(object):
    """
    Stimulator is used to stimulate a particular operation
    in the op nerve
    "I am not sure if it is still needed"
    
    """
    def __init__(self, op):
        self.x = None
        self.op = op
    
    def __call__(self, x):
        return self.op(x)


class Sub(Neuron):
    
    def __init__(self, index):
        super().__init__()
        self.index = index
    
    def __exec__(self, x):
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
    
    def __exec__(self, x):
        return self.stimulator(x)


class Noop(Neuron):
    """
    Noop neurons do not perform any operation
    """
    
    def spawn(self):
        return Noop()
    
    def __exec__(self, x):
        return x


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
            self.__exec__ = self._evaluate_ref
        else:
            self.__exec__ = self._evaluate
        """

    def spawn(self):
        return Emit(self._to_emit)

    def bot_backward(self, bot):
        bot(self)

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

    def __exec__(self, x):
        assert x is None, 'Emit Neurons must not take an input.'
        return self._to_emit
        # raise NotImplementedError(
        #    
        #)
        # if reference
        # execute reference and return


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
        # self.lhs = ops[0]
        # self.rhs = ops[-1]
        self.lhs, self.rhs = self._connect_ops(neurons)
        # self.ops = [to_neuron(op) for op in ops]
    
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
        if not isinstance(self.rhs, Out_):
            self.append(Out_())
        if not isinstance(self.lhs, In_):
            if not left_nil:
                self.prepend(In_())
            else:
                self.prepend(Nil_())
        
        return self

    def arm(self):
        return Arm(self)

    def bot_forward(self, bot):
        self.lhs.bot_forward(bot)
    
    def bot_backward(self, bot):
        self.rhs.bot_backward(bot)
    
    def spawn(self):
        cur = self.lhs
        ops = []
        while cur is not self.rhs:
            ops.append(cur.spawn())
            cur = cur.outgoing
        ops.append(cur.spawn())
        return Strand(ops)

    def __call__(self, x, bot=None):
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
    Arms are the basic Neuron encapsulator
    The purpose is so that they can
    """
    
    def __init__(self, strand):
        super().__init__()
        self.strand = strand.encapsulate()

    def strand(self):
        return self.strand

    def bot_forward(self, bot):
        self.strand.bot_forward(bot)
    
    def bot_backward(self, bot):
        self.strand.bot_backward(bot)

    def __exec__(self, x):
        return self.strand(x)

    def spawn(self):
        # Need to create this method
        return Arm(self.strand.spawn())

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
        Helper class used by tako to control the arms
        owner and parent should be contained in the flow not the op
        
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
        instance.x = 1
        instance.__armc__ = Tako._TakoAttr({}, instance, instance)
        prev_arm_controller = instance.__armc__
        while True:
            cur_arm_controller = cls._TakoAttr(cur.__arms__, cur, instance)
            prev_arm_controller.set_parent(cur_arm_controller)
            prev_arm_controller = cur_arm_controller

            cur = cur.__base__
            if not issubclass(cur, Tako) or cur != Tako:
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
            # Still need to check the
            # class
            pass
        
        cls = object.__getattribute__(self, '__class__')
        if hasattr(cls, k):
            v = getattr(cls, k)
            if is_arm(v):
                return object.__getattribute__(self, '__armc__').getarm(k)
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
        strand = In_() >> t
        
    class YType(type):
        
        def __new__(cls, name, bases, attr):
            return super().__new__(cls, name, bases, attr)

    print(X().strand(1))
    
    """
    # getting infinite recursion here. Need to check this out
    # Tako is resulting in a lot of recursion
    # print(X().strand)
    # print(type(strand.rhs))
    """
