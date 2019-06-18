from octako import bot

'''
Core Neuron Modules

A flow is the core component of the information
network

'''

class Neuron(object):
    '''
    Neuron is a node in an information network
    
    Neurons can be linked together to create a linked
    list (pipeline) of processes 
    in_ >> p1 >> p2 >> p3
    
    Each neuron must implement the spawn function
    which creates a neuron of the same type with the
    members passed to the constructor
    
    '''
    def __init__(self):
        self.incoming = None
        self.outgoing = None
    
    @property
    def key(self):
        return hash(self)
    
    def visit(self, bot):
        ''' 
        Visit this neuron with a bot
        :param Bot bot: The bot to visit the neuron with
        '''
        bot(self)
    
    def spawn(self):
        '''
        Spawn a new neuron of this type with the same member variables
        '''
        raise NotImplementedError
    
    def bot_forward(self, bot):
        '''
        Pass a bot forward through the network
        :param Bot bot: The bot to pass forward
        '''  
        self.visit(bot)
        if self.outgoing is not None:
            self.outgoing.bot_forward(bot)
    
    def forward(self, x, bot=None):
        '''
        Send an input forward through the network
        :param x: The input into the neuron
        :param Bot bot: The bot to send through the netwrok
        '''
        
        x = self(x, bot)
        if self.outgoing is not None:
            return self.outgoing.forward(x, bot)
        return x

    def connect(self, other):
        '''
        Connect this neuron (as the left hand side) to another neuron
        :param Neuron(able) other: The item to connect this neuron to
        '''
        other._connect_incoming(self)
        self._connect_outgoing(other)
    
    def _connect_incoming(self, other):
        '''
        Set the incoming of this neuron to be another neuron (a helper method for connect)
        :param Neuron(able) other: The item to connect this neuron to
        '''
        
        assert self.incoming is None, 'There can only be one incoming flow for a flow'
        self.incoming = other
        
    def _connect_outgoing(self, other):
        '''
        Set the outgoing of this neuron to be another neuron (a helper method for connect)
        :param other: The neuron tihs neuron feeds into
        '''
        assert self.outgoing is None, 'There can only be one incoming flow for a flow'
        self.outgoing = other

    def __call__(self, x, wh):
        '''
        Execute the operation specified by the neuron (In the base neuron there is no
        operation).
        :param x: The input into the neuron (can be anything)
        :param warehouse wh: a warehouse to pass through the network (can be used by
        neurons that store info or probe the bot for info).
        '''
        raise NotImplementedError


class _In(Neuron):
    '''
    A starting neuron for a Strand. _In indicates that there will be an input
    into the strand.
    
    _In is partly used for convenience so that operations which are not neurons
    will be converted to neurons
    
    It is also used along with _Out in order to have a start and end to the strand
    This is important for 'declarations' because the declarations will get
    replaced with other neurons and it is necessary to maintain the pointer to them.
    
    In practice
    
    in_ should be used which will create an _In neuron when doing rshift
    
    strand = in_ >> op1 >> op2 >> out_
    
    '''
    def __init__(self):
        super().__init__()
    
    def spawn(self):
        return _In()
    
    def _connect_incoming(self, other):
        raise AttributeError('An In flow cannot have any incoming neurons')
    
    def __getitem__(self, key):
        return to_neuron(Sub(key))

    def __rshift__(self, other):
        return Strand([self, other])
    
    def __call__(self, x, wh=None):
        return x


class _Out(Neuron):
    '''
    An ending neuron for a Strand.
    
    Used for convenience to create a strand which has declaration neurons
    '''
    def __init__(self):
        super().__init__()
    
    def spawn(self):
        return _Out()
    
    def _connect_outgoing(self, other):
        raise AttributeError('An In flow cannot have any incoming neurons')
    
    def bot_forward(self, bot):
        return

    def __getitem__(self, key):
        return to_neuron(Sub(key))

    def __rshift__(self, other):
        raise AttributeError('An "Out_" flow cannot output to another flow. ')
    
    def __call__(self, x, wh=None):
        return x


class _Nil(_In):
    '''
    A starting neuron for a Strand. _Nil indicates that there will be no
    input into the strand
    
    Primarily a convenience for creating 'strands' with Emit Neurons
    This is used as the starting flow for the case where there
    is no input into the network
    '''
    def __init__(self):
        super().__init__()
    
    def spawn(self):
        return _Nil()
    
    def _connect_incoming(self, other):
        raise AttributeError('A "Nil" flow cannot have any incoming neurons')

    def __getitem__(self, key):
        raise NotImplementedError

    def __rshift__(self, other):
        return Strand([self, other])
    
    def __call__(self, x, wh=None):
        assert x is None, 'The input to a Nil flow must be None'
        return x


class _InCreator(object):
    '''
    Convenience class to create an _In neuron using in_
    '''
    def __rshift__(self, other):
        return _In() >> other
    
    def __neuron__(self):
        return _In()


# used for starting a strand
in_ = _InCreator()


class _OutCreator(object):
    '''
    Convenience class to create an _Out neuron using out_
    '''
    def __rshift__(self, other):
        raise Exception(
            'Out neuron must be the final neuron.'
            )

    def __neuron__(self):
        return _Out()


# used for ending a strand
out_ = _OutCreator()


class _NilCreator(object):
    '''
    Convenience class to create an _Nil neuron using nil_
    '''
    def __rshift__(self, other):
        return _Nil() >> other

    def __neuron__(self):
        return _Nil()


# object used to create _Nil neurons
nil_ = _NilCreator()


class Sub(Neuron):
    '''
    Index the emission that has been passed in
    
    '''
    def __init__(self, index): 
        '''
        Neuron to call __getitem__ on the input that is passed in
        :param index: The index to retrieve
        '''
        super().__init__()
        self.index = index
    
    def __call__(self, x, wh=None):
        return x[self.index]
    
    def spawn(self):
        return Sub(self.index)


class OpNeuron(Neuron):
    '''
    Calls the object/function that is passed
    in as op
    '''
    def __init__(self, op):
        '''
        :param op: a callable (takes one parameter)
        '''
        super().__init__()
        self._op = op

    def spawn(self):
        return OpNeuron(self._op)
    
    def __call__(self, x, wh=None):
        return self._op(x)


class UnpackOpNeuron(OpNeuron):
    '''
    Calls the member operation unpacking the
    inputs that have been passed in
    '''
    def spawn(self):
        return UnpackOpNeuron(self._op)
    
    def __call__(self, x, wh=None):
        return self._op(*x)


class Noop(Neuron):
    '''
    Noop neurons do not perform any operation
    '''
    def spawn(self):
        return Noop()
    
    def __call__(self, x, wh=None):
        return x

# TODO: Refactor.. duplicating Stem
def _update_arg(arg, *args, **kwargs):
    if isinstance(arg, Arg):
        return arg.update(*args, **kwargs)
    else:
        return arg


class Arg(object):
    '''
    Args are used in stems to provide variable
    rather than constant arguments to the
    neurons created by the stem
    '''
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
    '''
    
    
    '''
    def __getattribute__(self, key):
        return Arg(key)

    def __getitem__(self, key):
        return Arg(key)


arg = _Arg()



# TODO: This is not right right now
class Declaration(Neuron):
    '''    
    Declaration will define a neural network
    
    '''
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
        self._kwargs = {k: _update_arg(arg, *args, **kwargs) for k, arg in self._kwargs.items()}
        self._args = [_update_arg(arg, *args, **kwargs) for arg in self._args]
        
    def define(self, x=None):
        '''
        '''
        if self.defined is not None:
            return self.defined
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

    def __call__(self, x, wh=None):
        if not self._dynamic and self.defined is None:
            neuron = self.define(x)
            self._replace(neuron)
            return neuron(x, wh)
        elif not self._dynamic:
            return self.defined(x, wh)
        else:
            return self.define(x)(x, wh)

    def spawn(self):
        return Declaration(
            self.module_cls, 
            self._args,
            self._kwargs,
            self._dynamic
            )


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
        updated_kwargs = {k: _update_arg(arg, kwargs) for k, arg in self._kwargs.items()}
        updated_args = [_update_arg(arg, *args, **kwargs) for arg in self._args]

        spawned = self._cls.spawn()
        # need to use a bot to update it for 
        update_args = bot.call.update_args(
            args, kwargs
            )
        spawned.bot_forward(update_args)
        return spawned


class Emit(Neuron):
    """
    Emit outputs the value that has been passed in
    It cannot have an incoming nerve as 
    """
    def __init__(self, to_emit):
        super().__init__()
        self._to_emit = to_emit

    def inform(self, x=None, bot=None):
        assert x is None, (
            'Cannot inform an Emit flow with a value ' +
            '(Must pass not value or None)'
            )
        return super().inform(x, bot)

    def __call__(self, x=None, wh=None):
        assert x is None, 'Emit Neurons must not take an input.'
        return self._to_emit

    def spawn(self):
        return Emit(self._to_emit)

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


'''
Strand and Arm are the core classes used to control flow. 
Arm encloses Strand into a flow
so that Arm can then be connected to other neurons
'''


class Strand(object):
    """
    Strand
    
    Strands are used for building process pipelines
    They are implemented as linked lists rather than
    lists.
    The reason for this is primarily because of the use of
    'declaration' neurons which get replaced.
    
    strand = in_ >> p1 >> p2 >> out_
    """
    def __init__(self, neurons):
        assert len(neurons) > 0, 'There must be more than one operation'
        self.lhs, self.rhs = self._connect_ops(neurons)

    def _connect_ops(self, neurons):
        '''
        Links a list of ops together in order to form a 'strand'
        
        '''
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
        '''
        :param index: Index of the neuron to retreive
        :return: neuron
        '''
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
    
    def append(self, neuronable):
        '''
        Attach the neuronable object to the 
        end of the strand
        '''
        rhs = to_neuron(neuronable)
        self.rhs.connect(rhs)
        self.rhs = rhs
    
    def prepend(self, neuronable):
        '''
        Attack the neuronable object to the
        beginning of the strand
        '''
        lhs = to_neuron(neuronable)
        lhs.connect(self.lhs)
        self.lhs = lhs

    def enclose(self, left_nil=False):
        '''
        Enclose the strand with an _In neuron
        on the front and an _Out neuron on the end.
        '''
        if not isinstance(self.rhs, _Out):
            self.append(_Out())
        if not isinstance(self.lhs, _In):
            if not left_nil:
                self.prepend(_In())
            else:
                self.prepend(_Nil())
        
        return self

    def arm(self):
        '''
        TODO: Consider whether the side effects (enclosing
        of the strand are permissible)
        Convert the Strand enclosing the strand
        (Remember that Arm will encloses the strand )
        :return: Arm
        '''
        return Arm(self)

    def bot_forward(self, bot):
        '''
        
        '''
        self.lhs.bot_forward(bot)
    
    def spawn(self):
        cur = self.lhs
        ops = []
        while cur is not self.rhs:
            ops.append(cur.spawn())
            cur = cur.outgoing
        ops.append(cur.spawn())
        return Strand(ops)

    def __call__(self, x=None, wh=None):
        return self.lhs.forward(x, wh)
    
    def __rshift__(self, other):
        '''
        
        :return Strand
        '''
        self.append(other)
        return self


Strand.__neuron__ = Strand.arm
        

def neuron_rshift(self, other):
    return Strand([self, other])


Neuron.__rshift__ = neuron_rshift


class Arm(Neuron):
    """
    Arms wrap strands so that they can be
    like neurons and concatentated to other
    processes.
    """
    def __init__(self, strand):
        super().__init__()
        self.strand = strand.enclose()

    def __call__(self, x, wh=None):
        return self.strand(x)
        
    def visit(self, bot):
        super().visit(bot)
        self.strand.bot_forward(bot)

    def spawn(self):
        return Arm(self.strand.spawn())
    
    @staticmethod
    def from_neuron(neuron):
        return Arm(Strand([neuron]))


'''
Tako modules allow for the creation of classes
that have arms defined in the class definition
rather than defining them in the constructor.
'''


def to_arm(val):
    '''
    Converts a strand to an arm if the parameters
    This is used for populating classes of type Tako
    
    :param val: the object to convert to an arm
    '''
    if isinstance(val, Strand):
        return Arm(val)

    assert isinstance(val, Arm), (
        'Input to to_arm must be "Arm" or "Strand"'
        )
    return val


def is_arm(v):
    return isinstance(v, Strand) or isinstance(v, Arm)


class _TakoType(type):
    '''
    Metaclass used for classes of type 
    Tako. It adds any class members of the
    type 'arm' or 'strand' to the Tako type.
    '''
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


class Tako(object, metaclass=_TakoType):
    '''
    
    '''
    class _TakoAttr(object):
        '''
        Helper class used by Tako to control the arms
        owner. It enables defining each arm
        in a similar manner methods with overrideing
        '''
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
            '''
            A 'SuperRef' will call this TakoAttr class when acting on it
            which will in turn call this TakoAttr if the attribute is an arm
            '''
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
    
    strand = (Neuron() >> Neuron() >> Neuron()).enclose()
    
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


class Warehouse(object):
    '''
    This type of bot is more passive, no?
    
    TODO: need to figure out how to deal with the case
    that a particular neuron is called by multiple 
    -- I added in probe_output ... I'm not sure if this is a
    -- good solution though because right now i am not setiting the output
    
    '''
    NO_OUTPUT = None, None
    
    def __init__(self):
        '''
        
        '''
        self._informed = None
        self.reset()

    def inform(self, key, val):
        self._informed[key] = val
    
    def probe(self, key, default=None):
        if key in self._informed:
            return self._informed[key], True
        return default, False
        
    def reset(self):
        self._informed = {}
    
    def uninform(self, key):
        self._informed.pop(key)

    def spawn(self):
        return Warehouse()
