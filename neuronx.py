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


# the base operation
Neuron.send_forward = Neuron._send_through_outgoing
# Base operation
Neuron.send_backward = Neuron._send_through_incoming


# case 1 -> strand
# case 2 -> nerve 
# case 3 -> other



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






class Flow(Neuron):
    """
    TODO: see if I need this type of flow
    
    """
    def send_forward(self, bot):
        raise NotImplementedError

    def send_backward(self, bot):
        """
        # needs to 
        """
        raise NotImplementedError




class Probe(Neuron):
    
    """
    Need to have better handling of ref types
    """
    
    def __init__(self, default=None, ref=''):
        # use default if output is none
        self._default = default
        if type(ref) != str:
            self._ref = to_neuron(ref)
            self._ref_type = 1
        else:
            self._ref = ref
            self._ref_type = 0

    def _get_key(self):
        if self._ref_type == 1:
            # should not need an input to get the 
            # ref.. should not be an input ref
            return self._ref.get_ref(None).get_key()
        else:
            return self._name

    def __exec__(self, x=None):
        assert self._ref_type == 1, (
            'Ref must be defined if not using a bot to' +
            'store the value to get.'
        )
        neuron = self._ref.get_ref(None)
        return neuron.output

    def __call__(self, x=None, bot=None):
        # need to consider this a little more
        
        if bot is not None:
            result = bot.probe(self._get_key())
            if result is not bot.NO_OUTPUT:
                return result[1] or self._default

        return super().__call__(x, bot) or self._default


class ProbeBot(Neuron):
    
    """
    Need to have better handling of ref types
    """
    def __call__(self, x=None, bot=None):
        # need to consider this a little more 
        result = bot.probe(self._get_key())
        if result is bot.NO_OUTPUT:
            return self._default
        return result[1]


class ProbeNeuron(Neuron):
    
    """
    Need to have better handling of ref types
    """
    def __exec__(self, x=None):
        neuron = self._ref.get_ref(None)
        return neuron.output or self._default

