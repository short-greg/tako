from __init__ import Neuron


class Delay(Neuron):
    
    def __init__(self, count=1, default=None, store_delay=False):
        assert count >= 1, 'The delay must be set to be greater than or equal to 1'
        self.default = default
        self.count = count
        self.vals = None
        self.reset_vals()
    
    def reset(self):
        self.vals = [self.default] * self.count
    
    def __call__(self, x, bot=None):
        # TODO: need to store delay here if necessary
        return super().__call__(x, bot)

    def __exec__(self, x):
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

    def bot_forward(self, bot):
        for n in self._modules:
            n.bot_forward(bot)

    """
    def send_backward(self, bot):
        for n in self._modules:
            n.send_backward(bot)
    """
    
    def __exec__(self, x):
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
    def __init__(self, cond=None, mod=None, pass_on=True):
        super().__init__()
        self._cond = mod(cond)
        self._mod = mod(mod)
        self._pass_on = pass_on

    def bot_forward(self, bot):
        self._cond.bot_forward(bot)
        self._mod.bot_forward(bot)

    def __exec__(self, x):
        passed = self._cond(x[0])
        
        if passed == self._pass_on:
            result = self._mod(x[1])
        else:
            result = None
        
        return [passed, result]

    """
    def send_backward(self, bot):
        self._cond.send_backward(bot)
        self._mod.send_backward(bot)
    """


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
        super.__init__()
        streams = args
        num_streams = len(streams) if args is not None else 0
        self._n = n or len(args)
        for i in range(self._n):
            if i < num_streams:
                self._modules.insert(to_neuron(num_streams[i]))
            else:
                self._modules.insert(to_neuron(None))

    def bot_forward(self, bot):
        for n in self._modules:
            n.bot_forward(bot)

    """
    def send_backward(self, bot):
        for n in self._modules:
            n.send_backward(bot)
    """

    def __exec__(self, x):
        result = []
        for cur_mod in self._modules:
            result.append(cur_mod(x))


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
    
    def __init__(self, mod, break_on=False, output_all=False):
        super().__init__()
        self._module = mod
        self._break_on = break_on
        self._output_all = output_all
    
    def __exec__(self, x):
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

    def bot_forward(self, bot):
        self._module.bot_forward(bot)

    """
    def send_backward(self, bot):
        self._module.send_backward(bot)
    """


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
        self._router = router
        self._modules = [mod(module) for module in args]
        self._default = mod(kwargs.get('default'))

    def bot_forward(self, bot):
        self._router.bot_forward(bot)
        for n in self._modules:
            n.bot_forward(bot)

    def __exec__(self, x):
        path = self._router(x[0])
        if path and self._modules[path]:
            return path, self._modules[path](x[1])
        elif self._default is not None:
            return path, self._default(x[1])
        else:
            return path, x[1]

    """
    def send_backward(self, bot):
        self._router.send_backward(bot)
        for n in self._modules:
            n.send_backward(bot)
    """

class Case(Neuron):
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
    
    def bot_forward(self, bot):
        for n in self._modules:
            n.bot_forward(bot)
        self._else.bot_forward(bot)
    
    def __exec__(self, x):
        output_ = self.NO_OUTPUT
        for i, module in enumerate(self._modules):
            output_ = module(x)
            if output_[0] == self._break_on:
                return i, output_
        
        if self._else is not None:
            return 'Else', self._else(x)
        return self.NO_OUTPUT
    
    """
    def send_backward(self, bot):
        self._router.send_backward(bot)
        for n in self._modules:
            n.send_backward(bot)
        self._else.send_backward(bot)
    """


"""
How to handle merge
1) I don't think I really need merge in anymore
2) Need to check if there is an output for the merge in the bot prior to executing
what if it's a reference?? <- This is a little more complcated
3) 
4) 
5) Call(my.x, args)

"""

class MergeIn(Neuron):
    def __init__(self, merge):
        self._merge = merge
    
    def __call__(self, x):
        return x


class _Merge(Neuron):
    def __init__(self, *args):
        # NEED to think about this more
        self._to_merge = [merge_in(arg, self) for arg in args]


class Onto(_Merge):
    
    def __exec__(self, x):
        return [
            x, *[nerve.probe() for nerve in self._to_merge]
        ]


class Under(_Merge):
    
    def __exec__(self, x):
        return [
            *[nerve.probe() for nerve in self._to_merge], x
        ]
