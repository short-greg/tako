"""
require 'oc.flow.pkg'
require 'oc.class'
require 'oc.nerve'
require 'oc.strand'
require 'oc.arm'
"""

"""




"""


from __init__ import Op, Neuron, Strand, neuron

class Strand(object):
    """
    # Not sure if this should be here
    
    """
    def __init__(self, lhs, rhs=None):
        self.lhs = lhs
        self.rhs = rhs or lhs
    
    def __getitem__(self, index):
        incoming = self.rhs.incoming
        ops = []
        while incoming is not None:
            ops.append(incoming)
        
        return ops[-(index + 1)]

    def encapsulate(self):
        self.rhs >> Out_()

    def arm(self):
        return Arm(self)

    def __call__(self, x, bot):
        self.lhs.inform(x, bot)
        return self.rhs.probe()
    
    def __rshift__(self, other):
        
        if isinstance(other, Strand):
            self.rhs.connect_to(other.lhs)
            strand = Strand(self.lhs, other.rhs)
        else:
            other = to_neuron(other)
            self.rhs.connect_to(other)
            strand = Strand(self.lhs, other)
        return strand


class Stimulator(object):
    def __init__(self, op):
        self.x = None
        self.op = op
    
    def __call__(self, x, bot=None):
        return self.op(x)



class Neuron(object):
    """
    The base neuron class
    
    """
    def _send_through_incoming(self, bot):
        if bot(self):
            for neuron in self.outgoing:
                neuron.send_forward(bot)
    
    def _send_through_outgoing(self, bot):
        if bot(self) and self.incoming is not None:
            self.incoming.send_backward(bot)
    
    def send_forward(self, bot):
        raise NotImplementedError

    def send_backward(self, bot):
        raise NotImplementedError

    def connect(self, other):
        other._connect_incoming(self)
        self._connect_outgoing(other)
    
    def _connect_incoming(self, other):
        assert self.incoming is None, 'There can only be one incoming neuron for a neuron'
        self.incoming = other
        
    def _connect_outgoing(self, other):
        self.outgoing.append(other)
    
    def replace_outgoing(self, to_replace, replace_with):
        for i, outgoing in enumerate(self.outgoing):
            if outgoing is to_replace:
                self.outgoing[i] = replace_with
                return
        # TODO Raise an error
    
    # for bot
    # use hash(self) <- get the hash for the neuron and 
    # pass it to the bot.. 
    # or just send the bot self... not sure which to do yet
    
    def inform(self, x, bot):
        self.x = x
    
    def probe(self, bot):
        raise NotImplementedError
    
    def __call__(self, x):
        raise NotImplementedError

# the base operation
Neuron.send_forward = Neuron._send_through_outgoing
# Base operation
Neuron.send_backward = Neuron._send_through_incoming
Neuron.__rshift__ = Strand.__rshift__

class Sub(Op):
    
    def __init__(self, index):
        self.index = index
    
    def __call__(self, x):
        return x[self.index]


# case 1 -> strand
# case 2 -> nerve 
# case 3 -> other


def to_neuron(x):
    if hasattr(x, '__neuron__'):
        return x.__neuron__()
    elif x is None:
        return Noop()
    
    # The default is to use an OpNeuron
    return OpNeuron(x)


def _prepare(x):
    if type(x) == Strand:
        return [*x]
    elif type(x) == Neuron:
        return [x]
    else:
        return [to_neuron(x)]


def concat(lhs, rhs):
    
    lhs = _prepare(lhs)
    rhs = _prepare(rhs)
    return Strand([*lhs, *rhs])

Neuron.__rshift__ = Strand.__rshift__   

def get_item(self, index):
    sub = Sub(index)
    return self>>sub


class OpNeuron(Neuron):
    """
    Op neuron calls an particular operation
    """
    def __init__(self, op, stimulator_cls=None):
        self.incoming = None
        self.outgoing = list()
        if stimulator_cls is not None:
            self.stimulator = stimulator_cls(op)
        else:
            self.stimulator = Stimulator(op)

    def probe(self, bot):
        x = None
        if self.x is not None:
            x = self.x
        elif self.incoming is not None:
            x = self.incoming.probe()
        return self.stimulator.op(x, bot)
    
    def __call__(self, x):
        return self.stimulator(x)


class Noop(Neuron):
    """
    Noop neurons do not perform any operation
    """
    def __init__(self):
        self.incoming = None
        self.outgoing = list()
    
    def send_forward(self, bot):
        if bot(self):
            for neuron in self.outgoing:
                neuron.send_forward(bot)

    def send_backward(self, bot):
        if bot(self) and self.incoming is not None:
            self.incoming.send_backward(bot)

    def probe(self, bot=None):
        x = None
        if self.x is not None:
            x = self.x
        elif self.incoming is not None:
            x = self.incoming.probe()
        return x
    
    def __call__(self, x):
        return x


class Emit(Neuron):
    """
    Emit outputs the value that has been passed in
    It cannot have an incoming nerve as 
    """
    def __init__(self, to_emit):
        self._to_emit = to_emit
        if isinstance(to_emit, Ref):
            self.__call__ = self._evaluate_ref
        else:
            self.__call__ = self._evaluate

    def send_forward(self, bot):
        if bot(self):
            for neuron in self.outgoing:
                neuron.send_forward(bot)

    def send_backward(self, bot):
        bot(self)
    
    def probe(self, bot=None):
        x = None
        if self.x is not None:
            x = self.x
        return self.stimulator.op(x, bot)

    def inform(self, x=None, bot=None):
        assert x is None, 'Cannot inform an Emit neuron with a value (Must pass not value or None)'

    def _evaluate(self):
        return self._to_emit
    
    def _evaluate_ref(self):
        return self._to_emit()
        
    def __call__(self):
        raise NotImplementedError(
            'The call method should be defined on initialization'
        )
        # if reference
        # execute reference and return

class In_(Neuron):
    """
    Used for convenience to create a strand where the following objects are
    'ops' so that those ops will properly be converted to neurons
    """
    def __init__(self):
        super().__init__(Noop)
    
    def _connect_incoming(self, other):
        raise AttributeError('An In neuron cannot have any incoming neurons')
    
    def probe(self, bot):
        return self.x
    
    def __getitem__(self, key):
        return to_neuron(Sub(key))

    def __rshift__(self, other):
        return Strand(self, to_neuron(other))


class Out_(Neuron):
    """
    Used for convenience to create a strand where the following objects are
    'ops' so that those ops will properly be converted to neurons
    """
    def __init__(self):
        super().__init__(Noop)
    
    def _connect_outgoing(self, other):
        raise AttributeError('An In neuron cannot have any incoming neurons')
    
    def probe(self, bot):
        return self.x

    def __getitem__(self, key):
        return to_neuron(Sub(key))

    def __rshift__(self, other):
        raise AttributeError('An "Out_" neuron cannot output to another neuron. ')



class Nil_(In_):
    """
    Primarily a convenience for creating 'strands' with Emit Neurons
    TODO: consider removing this now that Emit is a 'neuron' rather than an op
    """
    def __init__(self):
        super().__init__()
    
    def _connect_incoming(self, other):
        raise AttributeError('A "Nil" neuron cannot have any incoming neurons')
    
    def inform(self, x=None, bot=None):
        assert x is None, 'Cannot inform nil Neuron'
    
    def probe(self, bot=None):
        return None

    def __getitem__(self, key):
        raise NotImplementedError

    def __rshift__(self, other):
        return Strand(self, to_neuron(other))


class Flow(Neuron):
    """
    TODO: see if I need this type of neuron
    
    """
    def send_forward(self, bot):
        raise NotImplementedError

    def send_backward(self, bot):
        """
        # needs to 
        """
        raise NotImplementedError


class Arm(Flow):
    
    def __init__(self, strand):
        self.strand = strand

    def strand(self):
        return self.strand

    def send_forward(self, bot):
        self.lhs.send_forward(bot)
    
    def send_backward(self, bot):
        self.rhs.send_backward(bot)

    def __call__(self, x, bot=None):
        return self.strand(x, bot)


class Delay(Flow):
    
    def __init__(self, count=1, default=None):
        assert count >= 1, 'The delay must be set to be greater than or equal to 1'
        self.default = default
        self.count = count
        self.vals = None
        self.reset_vals()
    
    def reset(self):
        self.vals = [self.default] * self.count

    def __call__(self, x, bot=None):
        # 
        # if bot:
        # vals = bot.get(hash(self))
        # cur = vals.pop(0)
        # vals.append(x)
        # bot.set(hash(self), vals)
        # return cur
        
        cur = self.vals.pop(0)
        self.vals.append(x)
        return cur


class Diverge(Flow):
    """
    --- A flow structure that sends each 
    -- emission through a different
    -- processing stream.  
    -- The number of emissions must equal that
    -- of the number of processing streams.
    -- @input   [values] (whatever the process 
    --          associated with the value at 
    --          index i takes
    -- @output  [values]
    -- @usage oc.Const({1, 2, 3}) .. oc.Diverge{
    --            p1, p2, p3
    --          }
    --          This will send 1, 2, and 3 through
    --          p1, p2, p3 respectively.
    """
    
    """
    --- private method to determine how many 
    -- times to loop
    """
    def __init__(self, n=None, *args):
        """
        --- @constructor
        -- @param    streams - Each of the processing 
        -- modules to process the emissions - {nn.Module}
        --  - Nerve | Strand
        -- @param streams.n - number of modules 
        -- (if not defined will be table.maxn of streams)
        """
        streams = args
        super().__init__(self._DivergeStimulator())
        self._modules = []
        num_streams = len(streams)
        self._n = n or num_streams
        for i in range(self._n):
            if i < num_streams:
                self._modules.append(to_neuron(streams[i]))
            else:
                self._modules.append(to_neuron(None))

    def send_forward(self, bot):
        for n in self._modules:
            n.send_forward(bot)

    def send_backward(self, bot):
        for n in self._modules:
            n.send_backward(bot)
    
    def __call__(self, x):
        """
        Right now x needs to be the same length as the number of modules
        
        --- Send each index of the input through the
        -- corresponding strand index.
        -- @param input - {}
        """
        result = []
        for i in range(self._n):
            result.append(
                self._modules[i](x[i])
            )
        return result


class Gate(Flow):
    """
    --- Control structure that passes the outputs based on
    -- whether a condition is passed 
    -- (similar to an if-statement)
    --
    -- Nerve: Can be set to probe or stimulate with the input
    -- Function: Can be set to send the input through 
    --            the function
    -- format: function (self, input) ... end
    --
    -- @input - The value that gets passed in
    -- @output - {passed?, <stream output>} - 
    --            {boolean, <stream output>} - 
    -- 
    -- @usage  oc.Gate(
    --   function (self, input) return input ~= nil end,
    --   nn.Linear(2, 2)
    -- )
    """
    def __init__(self, cond=None, mod=None, pass_on=True):
        super().__init__()
        self._cond = mod(cond)
        self._mod = mod(mod)
        self._pass_on = pass_on

    def send_forward(self, bot):
        self._cond.send_forward(bot)
        self._mod.send_forward(bot)

    def send_backward(self, bot):
        self._cond.send_backward(bot)
        self._mod.send_backward(bot)

    def __call__(self, x):
        passed = self._cond(x[0])
        
        if passed == self._pass_on:
            result = self._mod(x[1])
        else:
            result = None
        
        return [passed, result]


class Multi(Flow):
    """
    --- Multi sends an input through several 
    -- processing
    -- 
    -- @input - value (will be sent through each stream)
    -- @output - []
    -- 
    -- @example oc.Var(1) .. oc.Multi{n=3}
    -- Probing will result in the output {1, 1, 1}
    -- The number of processes is specified to be
    -- 3 but they are all Noops
    --
    -- @example oc.Var(1) .. oc.Multi{p1, p2, p3}
    -- Here the output will be {
    --   p1:stimulate(1),
    --   p2:stimulate(1),
    --   p3:stimulate(1)
    -- }
    """
    def __init__(self, n=None, *args):
        super.__init__()
        streams = args
        num_streams = len(streams) if args is not None else 0
        self._n = n or len(args)
        for i in range(self._n):
            if i < num_streams:
                self._modules.insert(to_neuron(num_streams[i]))
            else:
                self._modules.insert(to_neuron(None))

    def send_forward(self, bot):
        for n in self._modules:
            n.send_forward(bot)

    def send_backward(self, bot):
        for n in self._modules:
            n.send_backward(bot)

    def __call__(self, x=None):
        result = []
        for cur_mod in self._modules:
            result.append(cur_mod(x))


class Repeat(Flow):
    """
    --- Repeat a process until the process outputs false
    -- It is possible to update the gradient of
    -- the process through updateOutput if 
    -- gradOn is set to true.  The stream will 
    -- repeatedly be informed by the input that 
    -- is passed in.  Repeat executes
    -- backpropagation and accumulation as 
    -- well if they are turned on.
    -- @input Whatever the inner process takes
    -- @output nil
    -- @usage oc.Repeat(
    --             oc.ref.getResponse():eq('Finished')
    --        )
    """
    
    def __init__(self, mod, break_on=False, output_all=False):
        super().__init__()
        self._module = mod
        self._break_on = break_on
        self._output_all = output_all
    
    def __call__(self, x):
        all_results = []
        result = None
        
        while True:
            cur_result = self._module(x)
            if self._output_all:
                all_results.append(result)
                result = all_results
            else:
                result = cur_result
            
            if cur_result[0] == self._break_on:
                break

        return result

    def send_forward(self, bot):
        self._module.send_forward(bot)

    def send_backward(self, bot):
        self._module.send_backward(bot)


class Switch(Flow):
    """
    --- @abstract
    --
    -- Control module that sends data
    -- through a single process amongst several 
    -- processes.  There are two types of routers: 
    -- Switch and Case.  
    -- 
    -- Case works like an IfElse block and
    -- where the first Case to succeed gets output
    -- Switch has a nerve which outputs the 
    -- path to be taken.
    -- TODO: Some unit tests are broken.. 
    -- Need to look into this problem 

    --
    
    --- Control module that sends data
    -- through a function which routes the input
    -- to one of n nerves where n is the number
    -- of processes.
    --
    -- @usage oc.Switch(
    --   router,
    --   {p1, p2, p3}
    -- )
    -- This Switch will send the input through
    -- router which outputs a number representing
    -- the path to take.  If p2 is chosen the output
    --　will be {path, p2.output}
    --
    -- @input depends on the nerves
    -- @output {path, nerve[path].output[2]}
    --
    
    -- TODO: the switch backpropagation is
    -- not correct right now.  If the default value
    -- is output... it should still output the
    -- actual value that is output and not 'defualt'
    -- i think
    
    """
    def __init__(self, router, *args, **kwargs):
        super().__init__()
        self._router = router
        self._modules = [mod(module) for module in args]
        self._default = mod(kwargs.get('default'))
    
    def __call__(self, x):
        path = self._router(x[0])
        if path and self._modules[path]:
            return path, self._modules[path](x[1])
        elif self._default is not None:
            return path, self._default(x[1])
        else:
            return path, x[1]

    def send_forward(self, bot):
        self._router.send_forward(bot)
        for n in self._modules:
            n.send_forward(bot)

    def send_backward(self, bot):
        self._router.send_backward(bot)
        for n in self._modules:
            n.send_backward(bot)


class Case(Flow):
    """
    --- Control module that sends the input
    -- through processes one by one 
    -- if the process outputs success then
    -- that output will become the output of
    -- the Case
    --
    -- @usage oc.Case{
    --   oc.Gate{p1, p2},
    --   oc.Gate{p3, p4},
    --   default=p5
    -- }
    -- This Case will send through Gate1 and
    -- if its first output is true then it will 
    -- the {path, p2.output}
    --
    -- @input depends on the nerves
    -- @output {path, nerve[path].output[2]}
    --     
    -- TODO: Some unit tests are broken.. 
    -- Need to look into this problem
    """
    NO_OUTPUT = None, None
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._modules = [to_neuron(module) for module in args]
        self._else = kwargs.get('else')
        if self._else is not None:
            self._else = mod(self._else)
        self._break_on = kwargs.get('break_on', True)
    
    def send_forward(self, bot):
        for n in self._modules:
            n.send_forward(bot)
        self._else.send_forward(bot)

    def send_backward(self, bot):
        self._router.send_backward(bot)
        for n in self._modules:
            n.send_backward(bot)
        self._else.send_backward(bot)
    
    def __call__(self, x):
        output_ = self.NO_OUTPUT
        for i, module in enumerate(self._modules):
            output_ = module(x)
            if output_[0] == self._break_on:
                return i, output_
        
        if self._else is not None:
            return 'Else', self._else(x)
        return self.NO_OUTPUT


class MergeIn(Op):
    def __init__(self, merge):
        self._merge = merge
    
    def __call__(self, x):
        return x


class _Merge(Flow):
    def __init__(self, *args):
        # NEED to think about this more
        self._to_merge = [merge_in(arg, self) for arg in args]


class Onto(_Merge):
    
    def __call__(self, x):
        return [
            x, *[nerve.probe() for nerve in self._to_merge]
        ]


class Under(_Merge):
    
    def __call__(self, x):
        return [
            *[nerve.probe() for nerve in self._to_merge], x
        ]


