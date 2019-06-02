from tako import Neuron, to_neuron, Strand, Arm
from tako import ref


def to_strand(neuron):
    return Strand([neuron]).encapsulate()


class Delay(Neuron):
    
    def __init__(self, count=1, default=None):
        assert count >= 1, 'The delay must be set to be greater than or equal to 1'
        self.default = default
        self.count = count
        self.vals = None
        self.reset()
    
    @property
    def count(self):
        return self._count
    
    @count.setter
    def count(self, v):
        assert v > 0, (
            'The amount of delay must be ' +
            'greater than 0.'
        )
        self._count = v
    
    def reset(self):
        self.vals = [self.default] * self.count

    def __call__(self, x, bot=None):
        cur = self.vals.pop(0)
        self.vals.append(x)
        return cur

class Diverge(Neuron):
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
        print(args, n)
        super().__init__()
        streams = args
        self._modules = []
        num_streams = len(streams)
        self._n = n or num_streams
        for i in range(self._n):
            if i < num_streams:
                self._modules.append(to_neuron(streams[i]))
            else:
                self._modules.append(to_neuron(None))

    def bot_forward(self, bot):
        for n in self._modules:
            n.bot_forward(bot)
    
    def __call__(self, x, bot=None):
        """
        Right now x needs to be the same length as the number of modules
        
        --- Send each index of the input through the
        -- corresponding strand index.
        -- @param input - {}
        """
        result = []
        for i in range(self._n):
            result.append(
                self._modules[i](x[i], bot)
            )
        return result


class Gate(Neuron):
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
    def __init__(self, cond=None, neuron=None, pass_on=True):
        super().__init__()
        self._cond = to_strand(cond)
        self._neuron = to_strand(neuron)
        self._pass_on = pass_on

    def bot_forward(self, bot):
        self._cond.bot_forward(bot)
        self._mod.bot_forward(bot)

    def __call__(self, x, bot=None):
        passed = self._cond(x[0]) == self._pass_on
        
        if passed:
            result = self._neuron(x[1], bot)
        else:
            result = None
        
        return [passed, result]


class Multi(Neuron):
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
        super().__init__()
        streams = args
        num_streams = len(streams) if args is not None else 0
        self._n = n or num_streams
        assert num_streams <= self._n, (
            'Cannot '
        )
        self._modules = []
        for i in range(self._n):
            if i < num_streams:
                self._modules.append(to_neuron(args[i]))
            else:
                self._modules.append(to_neuron(None))

    def bot_forward(self, bot):
        for n in self._modules:
            n.bot_forward(bot)

    def __call__(self, x, bot=None):
        result = []
        for cur_mod in self._modules:
            result.append(cur_mod(x, bot))
        return result


class Repeat(Neuron):
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
    
    # TODO: How to send the bot forward through the network???
    # Is this straightforward? Do I need to store the output
    # at each time step? <- I think I don't...
    # I just need to figure out how to use the delay functionality
    
    def __init__(self, mod, break_on=False, output_all=False):
        super().__init__()
        self._module = mod
        self._break_on = break_on
        self._output_all = output_all
    
    def __call__(self, x, bot=None):
        all_results = []
        result = None
        
        while True:
            cur_result = self._module(x, bot)
            if self._output_all:
                all_results.append(result)
                result = all_results
            else:
                result = cur_result
            
            if cur_result[0] == self._break_on:
                break

        return result

    def bot_forward(self, bot):
        self._module.bot_forward(bot)


class Switch(Neuron):
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
        self._router = to_strand(router)
        self._modules = [to_strand(module) for module in args]
        default = kwargs.get('default')
        self._default = to_strand(default) if default is not None else None

    def bot_forward(self, bot):
        self._router.bot_forward(bot)
        for n in self._modules:
            n.bot_forward(bot)

    def __call__(self, x, bot=None):
        path = self._router(x[0])
        print(path)
        if 0 <= path <= len(self._modules):
            return path, self._modules[path](x[1], bot)
        elif self._default is not None:
            return path, self._default(x[1], bot)
        else:
            return path, x[1]


class Cases(Neuron):
    """
    --- Control module that sends the input
    -- through processes one by one 
    -- if the process outputs success then
    -- that output will become the output of
    -- the Case
    --
    -- @usage oc.Cases(
    --   oc.Gate{p1, p2},
    --   oc.Gate{p3, p4},
    --   default=p5
    -- )
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
        self._modules = [to_strand(module) for module in args]
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
        for i, module in enumerate(self._modules):
            output_ = module(x, bot)
            if output_[0] == self._break_on:
                return i, output_[1]
        
        if self._else is not None:
            return 'Else', self._else(x, bot)
        return self.NO_OUTPUT


"""
How to handle merge
1) I don't think I really need merge in anymore
2) Need to check if there is an output for the merge in the bot prior to executing
what if it's a reference?? <- This is a little more complcated
3) 
4) 
5) Call(my.x, args)

"""

class _Merge(Neuron):
    """
    
    
    """
    def __init__(self, *args):
        # NEED to think about this more
        self._to_merge = [to_strand(arg) for arg in args]
    
    """
    def _get_output(self, neuron, bot):
        y, exists = neuron.probe_output(bot)
        
        if not exists:
            return neuron()
        return y
    """


class Onto(_Merge):
    """
    """
    def __call__(self, x, bot=None):
        return [
            x, *[strand(None, bot) for strand in self._to_merge]
        ]


class Under(_Merge):
    """
    """
    def __call__(self, x, bot=None):
        return [
            *[strand(None, bot) for strand in self._to_merge], x
        ]


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

class BotInform(Neuron):
    def __init__(self, neuronable, name='', use_neuron_key=True, auto_reset=True):
        self._base = to_neuron(neuronable)
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

    def __call__(self, x, bot=None):
        key = self.key
        if not self._auto_reset:
            y, found = bot.probe(key)
            if found:
                return y
        y = self._strand(x, bot)
        bot.inform(key, y)
        return y


class BotProbe(Neuron):
    def __init__(self, my_ref=None, name='', default=None):
        if my_ref is not None:
            # if it's of ref type then use to_neuron otherwise
            # do not
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
        # if found:
        #    return y
        # return __init__().__call__(x, bot)


class Store(Neuron):
    def __init__(self, neuronable, default=None):
        neuron = to_neuron(neuronable)
        self._strand = to_strand(neuron)
        self.output = None
        self._default = default
        self.reset()
    
    def reset(self):
        self.output = self._default
    
    def __call__(self, x, bot=None):
        y = self._strand(x, bot)
        self.output = y
        return y
