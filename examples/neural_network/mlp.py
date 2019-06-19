'''

Note: This example depends on Torch
'''

# import octako
import torch
import octako as tako
from octako import decl as D
# import octako.ref as ref
from octako.ref import r
from octako import ref
from torch import nn
from octako import in_, nil_
from octako import flow


criterion_neuron = tako.Stem(
    tako.OpNeuron.d(tako.arg[0], tako.UnpackStimulator.d())
)


class MNISTMLP(tako.Tako):
    '''
    
    '''
    layer1 = in_ >> D(nn.Linear, 784, 32) >> D(nn.Sigmoid)
    layer2 = in_ >> D(nn.Linear, 32, 10) >> D(nn.Softmax)
    predict = in_ >> r(ref.my.layer1) >> r(ref.my.layer2)
    update = (
        in_ >> flow.Diverge(
            r(ref.my.predict), None
        ) >> 
        criterion_neuron(nn.MSELoss()) >> 
        flow.Multi(
                None,
                ref.emission.backward()
            )[0]
        )
    
    def __init__(self):
        self.optim = torch.optim.Adam()
        
    def fit(self, dl, epochs=5, lr=1e-2):
        for i in range(len(epochs)):
            for X, y in dl:
                self.update((X, y))
                self.optim.step()
                self.optim.zero_grad()


# create the dataloader

