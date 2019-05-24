from torch import nn
from tako_ import iterator_exception, declaration, get_item, Neuron, neuron, _In


nn.Module.__rshift__ = Nerve.__rshift__
nn.Module.nerve = nerve
nn.Module.__getitem__ = get_item
nn.Module.iterator = iterator_exception
nn.Module.d = declaration



class TensorIn(_In):
    # For inputting a tensor into the network
    pass

