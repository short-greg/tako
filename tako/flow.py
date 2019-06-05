from tako import Neuron, to_neuron, Strand, Arm
from tako import ref


def to_strand(neuron):
    return Strand([neuron]).encapsulate()


class Diverge(Neuron):
    '''
    A flow structure that sends each emission
    through a different processing strand
    The number of emissions must be equal
    to the number of strands
    
    
    :@example:
      strand = nil_ >> Emit([1, 2, 3]) >> oc.Diverge{
        p1, p2, p3
      }
    This will send 1, 2, and 3 through 
    p1, p2, p3 respectively.
    '''
    def __init__(self, n=None, *args):
        """
        --- @constructor
        -- @param    streams - Each of the processing 
        -- modules to process the emissions - {nn.Module}
        --  - Nerve | Strand
        -- @param streams.n - number of modules 
        -- (if not defined will be table.maxn of streams)
        """
        super().__init__()
        streams = args
        self._strands = []
        num_streams = len(streams)
        self._n = n or num_streams
        for i in range(self._n):
            if i < num_streams:
                self._strands.append(to_neuron(streams[i]))
            else:
                self._strands.append(to_neuron(None))

    def bot_forward(self, bot):
        for strand in self._strands:
            strand.bot_forward(bot)
    
    def __call__(self, x, bot=None):
        '''
        :param x: must be a sequence with the same length
        as the number of strands
        '''
        result = []
        for i in range(self._n):
            result.append(
                self._strands[i](x[i], bot)
            )
        return result

    def spawn(self):
        return Diverge(
            self._n, 
            *[strand.spawn() for strand in self._strands]
        )


class Gate(Neuron):
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

    def bot_forward(self, bot):
        self._cond.bot_forward(bot)
        self._mod.bot_forward(bot)

    def __call__(self, x, bot=None):
        '''
        :param x: sequence with two items
        :param bot:
        :return passed, result: Whether the condition passed 
        and what the result is
        '''
        passed = self._cond(x[0]) == self._pass_on
        
        if passed:
            result = self._neuron(x[1], bot)
        else:
            result = None
        
        return passed, result
    
    def spawn(self):
        return Gate(
            cond=self._cond.spawn(), 
            neuron=self._neuron.spawn(),
            pass_on=self._pass_on
        )


class Multi(Neuron):
    '''
    Multi sends an input through several processing
    @input - value (will be sent through each stream)
    @output - []

    @example strand = in_ >> Emit(1) >> Multi(n=3)
    
    strand() -> [1, 1, 1]
    
    @example strand = in_ >> Emit(1) >> Multi(p1, p2, p3)
    Here the output will be [p1(1), p2(1), p3(1)]
    '''

    def __init__(self, n=None, *args):
        super().__init__()
        streams = args
        num_streams = len(streams) if args is not None else 0
        self._n = n or num_streams
        assert num_streams <= self._n, (
            'The number of streams must match or be less than "n".'
        )
        self._strands = []
        for i in range(self._n):
            if i < num_streams:
                self._strands.append(to_strand(args[i]))
            else:
                self._strands.append(to_strand(None))

    def bot_forward(self, bot):
        for n in self._strands:
            n.bot_forward(bot)

    def __call__(self, x, bot=None):
        result = []
        for cur_strand in self._strands:
            result.append(cur_strand(x, bot))
        return result

    def spawn(self):
        return Multi(
            self._n, 
            *[strand.spawn() for strand in self._strands]
        )


class Repeat(Neuron):
    '''
    Repeat a process until the process outputs
    false.
    
    @example 
    class Update(tako.Neuron):
        def __init__(self, lam, init_val=None):
            self._init_val = init_val
            self._lam = lam
            self._cur_val = self._init_val
        
        def __call__(self, x, bot=None):
            if self._cur_val is None:
                self._cur_val = x
            return lam(self._cur_val)
        
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

    # TODO: How to send the bot forward through the network???
    # Is this straightforward? Do I need to store the output
    # at each time step? <- I think I don't...
    # I just need to figure out how to use the delay functionality
    
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
    
    def __call__(self, x, bot=None):
        '''
        Repeatedly call self._stand until finished
        '''
        all_results = []
        result = None
        
        while True:
            cur_result = self._strand(x, bot)
            if self._output_all:
                all_results.append(result)
                result = all_results
            else:
                result = cur_result
            
            if cur_result[0] == self._break_on:
                break

        return result

    def bot_forward(self, bot):
        self._strand.bot_forward(bot)

    def spawn(self):
        return Repeat(self._strand.spawn(), self._break_on, self._output_all)


class Switch(Neuron):
    '''    
    Send the input[0] through a routing neuron
    which decides the neuron to send input[1]
    through

    @example in_ >> Switch(
      router,
      {p1, p2, p3}
    )
    '''
    def __init__(self, router, *args, **kwargs):
        super().__init__()
        self._router = to_strand(router)
        self._strands = [to_strand(module) for module in args]
        default = kwargs.get('default')
        self._default = to_strand(default) if default is not None else None

    def bot_forward(self, bot):
        self._router.bot_forward(bot)
        for n in self._strands:
            n.bot_forward(bot)

    def __call__(self, x, bot=None):
        path = self._router(x[0])
        if 0 <= path <= len(self._strands):
            return path, self._strands[path](x[1], bot)
        elif self._default is not None:
            return path, self._default(x[1], bot)
        else:
            return path, x[1]

    def spawn(self):
        return Switch(
            self._router.spawn(),
            *[strand.spawn() for strand in self._strands],
            default=self._default.spawn()
        )


class Cases(Neuron):
    '''
    Case works like an IfElse block and
    where the first Case to succeed gets output
    Control module that sends the input
    through processes one by one 
    if the process outputs success then
    that output will become the output of
    the Case

    @example oc.Cases(
        Gate(cond1, proc1),
        Gate{cond2, proc2),
        else_=proc3
    )
    '''
    NO_OUTPUT = None, None
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._strands = [to_strand(module) for module in args]
        self._else = kwargs.get('else_')
        if self._else is not None:
            self._else = to_neuron(self._else)
        self._break_on = kwargs.get('break_on', True)

    def bot_forward(self, bot):
        for n in self._modules:
            n.bot_forward(bot)
        self._else.bot_forward(bot)
    
    def __call__(self, x, bot=None):
        output_ = self.NO_OUTPUT
        for i, strand in enumerate(self._strands):
            output_ = strand(x, bot)
            if output_[0] == self._break_on:
                return i, output_[1]
        
        if self._else is not None:
            return 'Else', self._else(x, bot)
        return output_
    
    def spawn(self):
        return Cases(
            *[strand.spawn() for strand in self._strands], 
            else_=self._else.spawn() if self._else is not None else None
        )


class _Merge(Neuron):
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
        self._to_merge = [to_strand(arg) for arg in args]


class Onto(_Merge):
    """
    A merge which prepends the input in front of the merged
    items
    """
    def __call__(self, x, bot=None):
        return [
            x, *[strand(None, bot) for strand in self._to_merge]
        ]

    def spawn(self):
        return Onto([strand.spawn() for strand in self._to_merge])
    

class Under(_Merge):
    """
    A merge which appends the input to the back of the merged
    items
    """
    def __call__(self, x, bot=None):
        return [
            *[strand(None, bot) for strand in self._to_merge], x
        ]

    def spawn(self):
        return Under([strand.spawn() for strand in self._to_merge])


class BotInform(Neuron):
    '''
    Neuron that informs the bot that has been 
    passed through with the output of the neuron 
    (It has to be a warehouse)
    '''

    def __init__(self, neuronable, name='', use_neuron_key=True, auto_reset=True):
        '''
        :param neuronable: item to convert ot a neuron
        :param name: The name to use when informing (to attach to the key) - string
        :param use_neuron_key: Whether to use the neuron hash key when informing - boolean
        :param auto_reset: whether to update the output automatically when a new input is passed in -
        '''
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

    def bot_forward(self, bot):
        self._strand.bot_forward(bot)

    def __call__(self, x, bot=None):
        key = self.key
        if not self._auto_reset:
            y, found = bot.probe(key)
            if found:
                return y
        y = self._strand(x, bot)
        bot.inform(key, y)
        return y
    
    def spawn(self):
        return BotInform(
            self._strand.spawn(), self._name, 
            self._use_neuron_key, self._auto_reset
        )


class BotProbe(Neuron):
    def __init__(self, my_ref=None, name='', default=None):
        '''
        Neuron that informs the bot that has been 
        passed through with the output of the neuron 
        (It has to be a warehouse)
    
        :param (None or Neuron) my_ref: The neuron to refer to - if not specified will only use name
        :param string name: The name of the neuron to refer to 
        :param default: The default value to output (if the probe fails)
        '''
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

    def __call__(self, x, bot=None):
        assert x is None, (
            'x should not be defined when ' +
            'executing bot probe'
        )
        y, found = bot.probe(self.key)
        if not found:
            return self._default
        return y
    
    def spawn(self):
        return BotProbe(
            self._ref_base, self._name, self._default
        )


class Store(Neuron):
    '''
    Stores the output of a neuron as the attribute "output"
    '''
    def __init__(self, neuronable, default=None):
        neuron = to_neuron(neuronable)
        self._strand = to_strand(neuron)
        self.output = None
        self._default = default
        self.reset()
    
    def reset(self):
        self.output = self._default
    
    def bot_forward(self, bot):
        self._strand.bot_forward(bot)
    
    def __call__(self, x, bot=None):
        '''
        Call the "internal" strand and store the input
        '''
        y = self._strand(x, bot)
        self.output = y
        return y

    def spawn(self):
        return Store(
            self._strand.spawn(), self._name, self._default
        )


class Delay(Neuron):
    
    """Delays the input to be output at a later timestep
    
    Parameters
    ----------
    x : (some sort of input)

    Returns
    ----------
    x
    :example 
    """
    
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

    def __call__(self, x, bot=None):
        cur = self.vals.pop(0)
        self.vals.append(x)
        return cur

    def spawn(self):
        return Delay(
            self.count, self.default
        )


# class Adapter(Neuron):
    """
    Need to think a little more about this... and the how to handle
    the bot.. In flow nerves should a new bot be created??
    I'm thinking bots should be managed by each of them
    
    In this will want to have different bots i think
    I think it's okay actually
    diverge(
      my.x,
      my.x,
      my.y,
      my.y
    )
    
    flow.Adapter(
      -- out must be in in
      in_=[my.x, my.y, my.z], <- these must all be Arms/strands
      out=[my.z] or my.z <- 

      out_=[my.x, my.z], in_=[my.x, my.y, my.z]
    )
    
    .. 
    
    <- have to check if two references are the same.....
    <- storing the final output? <- this might make sense
    

    -- Not sure how to handle it for adapter yet
    
    bot.inform_extra <- can handle it in here <- inform what the bot is...


    x >> y >> BotStore(use_incoming=True)
    In_() >> z >> Onto() >> 
    In_() >> z >> BotStore()
    
    
    
    Problems..How to deal with updating
    """
    """
    def __init__(self, to_inform, to_probe):
        self._to_inform = to_neuron(to_inform)
        self._to_probe = to_neuron(to_probe)
        
        if type(to_inform) == 'list':
            self.__exec__ = self._exec_list
        else:
            self.__exec__ = self._exec_value
    
    def _inform(self):
        raise NotImplementedError('Inform method must be overwritten on construction.')
    
    def _probe(self):
        raise NotImplementedError('Probe method must be overwritten on construction.')
    
    def _exec_value(self, x, bot):
        self._to_inform(x)
    
    def _exec_list(self, x, bot):
        # x = In_() >> merge(my.z)
        # z = In_() >> Add(2)
        
        # call inform on each of the strands
        # however.. do not want to execute any of them twice
        # need to think about how to handle this
        
        # nerve ref <- can store the output in the bot??
        
        # diverge(my.x, my.x)
        
        my_hash = hash(self)
        for xi in x:
            if bot.informed_extra(my_hash, 'output'):
                return bot.probe_extra(my_hash, 'output')
            bot.inform_extra(hash(self), 'output', x)
        
        for to_inform, item in zip(self._to_inform, x):
            to_inform(item)
    
    def __exec__(self, x):
        raise NotImplementedError
    """
