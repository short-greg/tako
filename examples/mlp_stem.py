'''

Note: This example depends on Torch
'''

# import octako
import torch
from tako import decl as D
# import octako.ref as ref
from tako.ref import r
from torch import nn
from tako import in_, nil_
from tako import flow


criterion_neuron = octako.Stem(
    octako.OpNeuron.d(octako.arg[0], octako.UnpackStimulator.d())
)


update_stem = octako.Stem(
    flow.Diverge(
            r(octako.arg[0]), None
        ) >> 
        criterion_neuron(octako.arg[1]) >> 
        # output the loss but execute
        # backward
        flow.Multi(
                None,
                ref.emission.backward()
            )[0]
        )


class MNISTMLP(octako.Tako):
    '''
    
    '''
    layer1 = in_ >> D(nn.Linear, 784, 32) >> D(nn.Sigmoid)
    layer2 = in_ >> D(nn.Linear, 32, 10) >> D(nn.Softmax)
    predict = in_ >> r(ref.my.layer1) >> r(ref.my.layer2)
    update = update_stem(ref.my.predict, D(nn.BCELoss))

    def __init__(self):
        self.optim = torch.optim.Adam()
        
    def fit(self, dl, epochs=5, lr=-3):
        for i in range(len(epochs)):
            for X, y in dl:
                self.update((X, y))
                self.optim.step()
                self.optim.zero_grad()


# create the dataloader

