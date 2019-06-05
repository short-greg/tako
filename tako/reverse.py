import tako

'''
Reverse a particular nerve 
(can be used in autoencoders etc)
--
-- nn.Linear:rev(nn.Linear(2, 4)) -> this will create
--   an nn.Linear(4, 2) upon definition
-- 
-- self.arm.encoder = nn.Linear(2, 4)
-- self.arm.decoder = self.encoder:rev()
-- 
-- self.arm.autoencode = r(oc.my.encoder) .. r(oc.my.decoder)
-- 
-- self.autoencode:stimulate(torch.randn(2, 2)) -> will
--   output a 2 x 2 tensor
-- 
-- t:rev()
-- nn.Linear:rev() <- no module have to 
-- define dynamically overwrite the 
--
-- DeclarationReverse is used for declarations
-- n = nn.Linear:d(2, 4)
-- n:rev() -> creates a DeclarationReverse
'''

class Reverse(tako.Declaration):
    '''
    Reverse operation for a particular nerve
    The nerve should be defined within the 
    same Tako.
    --
    -- @param nerve - The nerve (or combination of 
    -- nerves to reverse) - oc.Nerve or {oc.Nerve}
    -- @param dynamic - Whether or not the nerve
    -- should be reversed with each update of the output
    -- If it is static, then the type of Reverse will
    -- change to the reversed nerve once it has been
    -- defined
    '''
    
    def __init__(self, neuron, dynamic=False):
        super().__init__(self)
        assert(
          type(dynamic) == 'boolean',
          'Argument dynamic must be of type boolean'
        )
        # what if it is a reference?
        super().__init__(neuron, dynamic=dynamic)
    
    def _reverse(self, x):
        return self._to_reverse.spawn()
    
    def define(self, x):
        reversed_neuron = self._reverse(x)
        self._defined = reversed_neuron
        return reversed_neuron


class DeclarationReverse(Reverse):
    '''
    --! @param
    
    '''
    def __init__(self, decl, dynamic):
        assert isinstance(decl, tako.Declaration)
        super().__init__(decl, dynamic)

    def define(self, x):
        defined = self.module_cls.define()
        reverser = defined.rev(self._dynamic)
        return reverser.define(x)


def _DeclRev(self, dynamic):
    return DeclarationReverse(self, dynamic)


def _NeuronRev(self, dynamic):
    return Reverse(self, dynamic)



# nn.Linear.d().rev()
# what if d is already defined?


tako.Neuron.rev = _NeuronRev
tako.Declaration.rev = _DeclRev
