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




