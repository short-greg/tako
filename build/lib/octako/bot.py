# TODO: Consider whether to continue to use
# has_visited since there cannot be loops anymore


class Bot(object):
    '''
    Bots are used in order to traverse the information network and perform
    operations on each of the neurons in the network
    '''
    
    def __init__(self):
        self._stop_on = None
        self._visited = {}
        
    def stop_on(self, neuron):
        '''
        Set a neuron that the bot should stop
        going forwraad on
        '''
        self._stop_on = neuron
    
    def has_visited(self, neuron):
        '''
        :param neuron: Neuron to check if visited
        :return boolean: whether the bot has visited a particular neuron
        '''
        return neuron in self._visited 
    
    def to_visit(self, neuron):
        '''
        :param neuron: neuron to check
        :return: whether the bot should visit a particular neuron
        '''
        
        return not self.has_visited(neuron) and self._stop_on is not neuron

    def reset(self):
        self._report = {}
        self.reset_visited()
    
    def reset_visited(self):
        self._visited = {}
    
    def _visit(self, neuron):
        '''
        Visit a particular neuron
        
        The base class doesn't do anything
        should override this behavior
        :param neuron: the neuron to visit
        '''
        pass

    def __call__(self, neuron):
        '''
        Visit the neuron if it has not been visited yet
        '''
        if self.to_visit(neuron):
            self._visit(neuron)
            self._visited[neuron] = True

    def report(self):
        return {}
    
    def spawn(self):
        NotImplementedError


class Call(Bot):
    '''
    Call is for creating a bot that
    will call a member of a nerve that it
    passes through.
    
    @usage call.relax() ->
    will create a bot that can
    relax nerves
    
    For 'class methods' use dot
    call.<func>(
        args={<arg>}
        cond=lambda nerve, func: hasattr(nerve, func)

    For 'instance methods' use colon and it will
    pass self as the first algorithm
    
    call.<func>(
        args={<arg>}
        cond=lambda nerve, func: hasattr(nerve, func)
    )
    Calls the function relax on all nerves
    '''
    
    def base_cond(self, neuron=None):
        return hasattr(neuron, self._func_name)

    def base_process(self, results):
        return results
  
    def base_report(self):
        return self._results
    
    def __init__(self, func_name, args=None, kwargs=None, cond=None, process=None, report=None):
        super().__init__()
        self._func_name = func_name
        self.cond = cond or self.base_cond
        self.report = report or self.base_report
        self.process = process or self.base_process
        self._results = {}
        self._args = args or []
        self._kwargs = kwargs or {}
    
    def to_visit(self, neuron):
        if super().to_visit(neuron):
            return self.cond(neuron)
        return False
    
    def _visit(self, neuron):
        result = object.__getattribute__(neuron, self._func_name)(*self._args, **self._kwargs)
        self._results[neuron] = self.process(result)
    
    def spawn(self):
        return Call(
            self._func_name, self._args, self.cond, self.process, self.report
            )


class _CallArgs(object):
    
    def __init__(self, func_name):
        self.func_name = func_name
    
    def __call__(self, *args, **kwargs):
        return Call(self.func_name, args=args, kwargs=kwargs)


class _CallFunc(object):
    
    def __getattr__(self, k):
        return _CallArgs(k)


call = _CallFunc()
