'''

Note: This example depends on Torch
'''

import tako
import torch
from tako import decl as D
import tako.ref as ref
from tako.ref import r
from torch import nn
from tako import in_, nil_
from tako import flow



criterion_neuron = tako.Stem(
    tako.OpNeuron.d(tako.arg[0], tako.UnpackStimulator.d())
)


class MNISTMLP(tako.Tako):
    '''
    
    '''
    layer1 = in_ >> D(nn.Linear, 784, 32) >> D(nn.Sigmoid)
    layer2 = in_ >> D(nn.Linear, 32, 10) >> D(nn.Softmax)
    predict = in_ >> r(ref.my.layer1) >> r(ref.my.layer2)
    update = in_ >> flow.Diverge(
            r(ref.my.predict), None
        ) >> 
        criterion_neuron(nn.MSELoss())) >> 
        flow.Multi(
                None,
                ref.emission.backward()
            )[0]
    
    def __init__(self):
        self.optim = torch.optim.Adam()
        
    def fit(self, dl, epochs=5, lr=):
        for i in range(len(epochs)):
            for X, y in dl:
                self.update((X, y))
                self.optim.step()
                self.optim.zero_grad()


# create the dataloader

