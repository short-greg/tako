from octako.core import Neuron, to_neuron, Strand, Arm
from octako import ref

# improve upon this to remove the side effects
def to_strand(neuron):
    if isinstance(neuron, Strand):
        strand = neuron
    else:
        strand = Strand([neuron])
        
    return strand.enclose()


class Flow(Neuron):
    '''
    Base class for flow neurons that contain
    other neurons
    '''
    def visit(self, bot):
        super().visit(bot)
        self.bot_down(bot)
    
    def bot_down(self, bot):
        raise NotImplementedError


class Diverge(Flow):
    '''
    A flow structure that sends each emission
    through a different processing strand
    The number of emissions must be equal
    to the number of strands
    
    
    :@example:
      strand = nil_ >> Emit([1, 2, 3]) >> Diverge{
        p1, p2, p3
      }
    This will send 1, 2, and 3 through 
    p1, p2, p3 respectively.
    '''
    def __init__(self, strands, n=None):
        """
        @constructor
        @param    streams - Each of the processing 
        modules to process the emissions - {nn.Module}
         - Nerve | Strand
        @param n - number of modules 
         (if not defined will be table.maxn of streams)
        """
        super().__init__()
        self._strands = []
        num_strands = len(strands)
        self._n = n or num_strands
        assert num_strands <= self._n, (
            'Argument n must be greater to or ' +
            'equal than the len(stands).'
            )
        for i in range(self._n):
            if i < num_strands:
                self._strands.append(to_neuron(strands[i]))
            else:
                self._strands.append(to_neuron(None))

    def bot_down(self, bot):
        for strand in self._strands:
            strand.bot_forward(bot)
    
    def __call__(self, x, wh=None):
        '''
        :param x: must be a sequence with the same length
        as the number of strands
        '''
        result = []
        for i in range(self._n):
            result.append(
                self._strands[i](x[i], wh)
            )
        return result

    def spawn(self):
        return Diverge(
            [strand.spawn() for strand in self._strands],
            self._n
        )


class Gate(Flow):
    '''
    Control structure that passes the output
    through a strand if it passes the condition
    Control structure that passes the outputs based on
    whether a condition is passed 
    (similar to an if-statement)

    @input - (val to pass to condition, val to pass to neuron)
    @output - {passed?, <stream output>} - 
              {boolean, <stream output>} - 
    @example  in_ >> Gate(
        cond=lambda x: x == 2,
        neuron=lambda x: x + 1
    )
    '''
    def __init__(self, cond=None, neuron=None, pass_on=True):
        '''
        :param cond: Condition required to pass for the input
        to go through the strand
        :param neuron: the operation to perform on inputs
        that pass
        :param pass_on: The value the output of cond
        should equal in order for the condition to pass
        '''
        super().__init__()
        self._cond = to_strand(cond)
        self._neuron = to_strand(neuron)
        self._pass_on = pass_on

    def bot_down(self, bot):
        self._cond.bot_forward(bot)
        self._neuron.bot_forward(bot)

    def __call__(self, x, wh=None):
        '''
        :param x: sequential with two items
        :return passed, result: Whether the condition passed 
        and what the result is
        '''
        passed = self._cond(x[0]) == self._pass_on
        if passed:
            result = self._neuron(x[1], wh)
        else:
            result = None
        
        return passed, result
    
    def spawn(self):
        return Gate(
            cond=self._cond.spawn(), 
            neuron=self._neuron.spawn(),
            pass_on=self._pass_on
        )


class Multi(Flow):
    '''
    Multi sends an input through several processing
    @input - value (will be sent through each stream)
    @output - []

    @example strand = in_ >> Emit(1) >> Multi(n=3)
    
    strand() -> [1, 1, 1]
    
    @example strand = in_ >> Emit(1) >> Multi(p1, p2, p3)
    Here the output will be [p1(1), p2(1), p3(1)]
    '''
    def __init__(self, strands=None, n=None):
        super().__init__()
        num_strands = len(strands) if strands is not None else 0
        self._n = n or num_strands
        assert num_strands <= self._n, (
            'The number of streams must match or be less than "n".'
        )
        self._strands = []
        for i in range(self._n):
            if i < num_strands:
                self._strands.append(to_strand(strands[i]))
            else:
                self._strands.append(to_strand(None))

    def bot_down(self, bot):
        for n in self._strands:
            n.bot_forward(bot)

    def __call__(self, x, wh=None):
        result = []
        for cur_strand in self._strands:
            result.append(cur_strand(x, wh))
        return result

    def spawn(self):
        return Multi(
            [strand.spawn() for strand in self._strands],
            self._n
        )


class Repeat(Flow):
    '''
    Repeat a process until the process outputs
    false.
    
    @example 
    class Update(octako.Neuron):
        def __init__(self, lam, init_val=None):
            self._init_val = init_val
            self._lam = lam
            self._cur_val = self._init_val
        
        def __call__(self, x, bot=None):
            if self._cur_val is None:
                self._cur_val = x
            return self._lam(self._cur_val)
        
        def spawn(self):
            return Update(self._lam, self._init_val)
    
    strand = in_ >> Repeat(
        Update(lambda x: x + 1, init_value=0) >>
        Gate(cond=lambda x: x == 3, neuron=lambda x: x + 1)
    )
    
    strand(0) -> 3

    strand = in_ >> Repeat(
        Update(lambda x: x + 1, init_value=0) >>
        Gate(cond=lambda x: x == 3, neuron=lambda x: x + 1), output_all=True
    )
    
    strand(0) -> [1, 2, 3]
    '''
    
    def __init__(self, neuron, break_on=False, output_all=False):
        '''
        :param neuron: The neuron to repeat
        :param break_on: the value to end the repeating on
        :param output_all: whether to output the results
        of each step of the "repeated" process
        '''
        super().__init__()
        self._neuron = neuron
        self._strand = to_strand(neuron)
        self._break_on = break_on
        self._output_all = output_all
    
    def __call__(self, x, wh=None):
        '''
        Repeatedly call self._stand until finished
        '''
        all_results = []
        result = None
        
        while True:
            cur_result = self._strand(x, wh)
            if self._output_all:
                all_results.append(cur_result[1])
                result = all_results
            else:
                result = cur_result[1]
            
            if cur_result[0] == self._break_on:
                break

        return result

    def bot_down(self, bot):
        self._strand.bot_forward(bot)

    def spawn(self):
        return Repeat(self._strand.spawn(), self._break_on, self._output_all)


class Switch(Flow):
    '''    
    Send the input[0] through a routing neuron
    which decides the neuron to send input[1]
    through

    @example 
    in_ >> Switch(
        router,
        {
            0: p1, 
            1: p2, 
            2: p3
        },
        default=p4
    )
    '''
    def __init__(self, router, paths, default=None):
        super().__init__()
        self._strands = {k: to_strand(neuron) for k, neuron in paths.items()}
        router = to_strand(router)
        self._default = to_strand(default) if default is not None else None
        self._router = router

    def bot_down(self, bot):
        self._router.bot_forward(bot)
        for key, neu in self._strands.items():
            neu.bot_forward(bot)
        self._default.bot_forward(bot)

    def __call__(self, x, wh=None):
        path = self._router(x[0])
        if path in self._strands:
            return path, self._strands[path](x[1], wh)
        elif self._default is not None:
            return path, self._default(x[1], wh)
        else:
            return path, x[1]

    def spawn(self):
        return Switch(
            self._router.spawn(),
            {k: strand.spawn() for k, strand in self._strands.items()},
            default=self._default.spawn()
            )


class Cases(Flow):
    '''
    Case works like an IfElse block and
    where the first Case to succeed gets output
    Control module that sends the input
    through processes one by one 
    if the process outputs success then
    that output will become the output of
    the Case

    @example oc.Cases(
        [
            Gate(cond1, proc1),
            Gate{cond2, proc2),
        ],
        default=proc3
    )
    '''
    NO_PATH = None
    DEFAULT_PATH = -1
    NO_OUTPUT = None
    
    def __init__(self, cases, default=None, pass_on=True):
        super().__init__()
        self._strands = [to_strand(neuron) for neuron in cases]
        self._default = default
        if self._default is not None:
            self._default = to_neuron(self._default)
        self._pass_on = pass_on

    def bot_down(self, bot):
        for strand in self._strands:
            strand.bot_forward(bot)
        self._default.bot_forward(bot)
    
    def __call__(self, x, wh=None):
        for i, strand in enumerate(self._strands):
            output_ = strand(x, wh)
            if output_[0] == self._pass_on:
                return i, output_[1]
        
        if self._default is not None:
            return self.DEFAULT_PATH, self._default(x, wh)
        return self.NO_PATH, self.NO_OUTPUT
    
    def spawn(self):
        return Cases(
            cases=[strand.spawn() for strand in self._strands], 
            default=self._default.spawn() if self._default is not None else None,
            pass_on=self._pass_on
        )


class _Merge(Flow):
    '''
    Merge in the output from another neuron
    The neuron must not need an input
    
    @example 
    strand1 = in_ >> BotInform(lambda x: x - 1, name='bot')
    strand2 = in_ >> lambda x: x + 1 >> Onto(BotProbe(name='bot', use_neuron_key=False))
    
    strand1(1, warehouse)
    strand2(1, warehouse) -> [2, 0]
    
    Merge can also be used with Emit
    strand = in_ >> lambda x: x + 1 >> Onto(Emit('bot'))
    
    strand(1) -> [2, 'bot']
    '''
    def __init__(self, *args):
        super().__init__()
        self._to_merge = [to_strand(arg) for arg in args]
    
    def bot_down(self, bot):
        for neuron in self._to_merge:
            neuron.bot_forward(bot)


class Onto(_Merge):
    """
    A merge which prepends the input in front of the merged
    items
    """
    def __call__(self, x, wh=None):
        return [
            x, *[strand(None, wh) for strand in self._to_merge]
        ]

    def spawn(self):
        return Onto(*[strand.spawn() for strand in self._to_merge])


class Under(_Merge):
    """
    A merge which appends the input to the back of the merged
    items
    """
    def __call__(self, x, wh=None):
        return [
            *[strand(None, wh) for strand in self._to_merge], x
        ]

    def spawn(self):
        return Under(*[strand.spawn() for strand in self._to_merge])


class BotInform(Flow):
    '''
    Neuron that informs the bot that has been 
    passed through with the output of the neuron 
    (It has to be a warehouse)
    '''

    def __init__(self, neuronable, name='', use_neuron_key=True, auto_reset=True):
        '''
        :param neuronable: item to convert ot a neuron
        :param string name: The name to use when informing (to attach to the key) - string
        :param bool use_neuron_key: Whether to use the neuron hash key when informing - boolean
        :param bool auto_reset: whether to update the output automatically when a new input is passed in -
        '''
        super().__init__()
        self._base = neuronable
        self._strand = to_strand(self._base)
        self._auto_reset = auto_reset
        self._name = name
        self._use_neuron_key = use_neuron_key
    
    @property
    def key(self):
        result = self._name
        if self._use_neuron_key is True:
            return result + str(hash(self))
        return result

    def bot_down(self, bot):
        self._strand.bot_forward(bot)

    def __call__(self, x, wh=None):
        key = self.key
        if not self._auto_reset:
            y, found = wh.probe(key)
            if found:
                return y
        y = self._strand(x, wh)
        wh.inform(key, y)
        return y
    
    def spawn(self):
        return BotInform(
            self._strand.spawn(), self._name, 
            self._use_neuron_key, self._auto_reset
        )


class BotProbe(Neuron):
    '''
    Neuron that retrieves data from a bot
    that a particular neuron set
    '''

    def __init__(self, my_ref=None, name='', default=None):
        '''
        Neuron that informs the bot that has been 
        passed through with the output of the neuron 
        (It has to be a warehouse)
    
        :param (None or Neuron) my_ref: The neuron to refer to - if not specified will only use name
        :param string name: The name of the neuron to refer to 
        :param default: The default value to output (if the probe fails)
        '''
        super().__init__()
        self._ref_base = my_ref
        
        if my_ref is not None:
            self._ref = to_neuron(my_ref)
        else:
            self._ref = None

        self._name = name
        self._default = default
    
    @property
    def key(self):
        result = self._name
        if self._ref is not None:
            if isinstance(self._ref, ref.RefBase):
                my_ref = self._ref(None)
            else:
                my_ref = self._ref
            return result + str(my_ref.key)
        return result

    def __call__(self, x, wh=None):
        assert x is None, (
            'x should not be defined when ' +
            'executing bot probe'
        )
        y, found = wh.probe(self.key)
        if not found:
            return self._default
        return y
    
    def spawn(self):
        return BotProbe(
            self._ref_base, self._name, self._default
        )


class Store(Flow):
    '''
    Stores the output of a neuron as the attribute "output"
    '''
    def __init__(self, neuronable, default=None):
        '''
        :param neuronable: item that can be changed to a neuron
        :param default: the default value to store
        '''
        super().__init__()
        neuron = to_neuron(neuronable)
        self._strand = to_strand(neuron)
        self.output = None
        self._default = default
        self.reset()
    
    def reset(self):
        self.output = self._default
    
    def bot_down(self, bot):
        self._strand.bot_forward(bot)
    
    def __call__(self, x, wh=None):
        '''
        Call the "internal" strand and store the input
        '''
        y = self._strand(x, wh)
        self.output = y
        return y

    def spawn(self):
        return Store(
            self._strand.spawn(), self._default
        )


class Delay(Neuron):
    '''
    Delays the input to be output at a later timestep
    
    Parameters
    ----------
    x : (some sort of input)

    Returns
    ----------
    x
    :example 
    '''
    def __init__(self, count=1, default=None):
        '''
        :param int count: The amount to delay by
        :param default: The default value to output when there is
        no input to output yet
        '''
        assert count >= 1, (
            'The delay must be set to be ' +
            'greater than or equal to 1'
        )
        self.default = default
        self.count = count
        self.vals = None
        self.reset()
    
    @property
    def count(self):
        return self._count
    
    @count.setter
    def count(self, v):
        '''
        Specify the delay count
        Must be creater than 0
        :param int v: The amount of delay
        '''
        assert v > 0, (
            'The amount of delay must be ' +
            'greater than 0.'
        )
        self._count = v
    
    def reset(self):
        '''
        :post: The values used for delay are reset
        to the default values
        '''
        self.vals = [self.default] * self.count

    def __call__(self, x, wh=None):
        cur = self.vals.pop(0)
        self.vals.append(x)
        return cur

    def spawn(self):
        return Delay(
            self.count, self.default
        )
