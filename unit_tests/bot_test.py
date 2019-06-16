import tako.bot as bot
import tako


class NeuronTest(tako.Noop):
    
    def __init__(self):
        super().__init__()
        self.i = 1
    
    def reset(self, x=0):
        self.i = x

    def get(self):
        return self.i


class TestCall(object):
    
    def test_call_func(self):
        neuron1 = NeuronTest()
        neuron2 = NeuronTest()
        strand = neuron1 >> neuron2
        call_bot = bot.call.reset()
        strand.bot_forward(call_bot)
        assert neuron1.i == 0
        assert neuron2.i == 0

    def test_call_func_with_args(self):
        neuron1 = NeuronTest()
        neuron2 = NeuronTest()
        strand = neuron1 >> neuron2
        call_bot = bot.Call(
            'reset', args=[4]
            )
        strand.bot_forward(call_bot)
        assert neuron1.i == 4
        assert neuron2.i == 4

    def test_call_func_with_kwargs(self):
        neuron1 = NeuronTest()
        neuron2 = NeuronTest()
        strand = neuron1 >> neuron2
        call_bot = bot.Call(
            'reset', kwargs=dict(x=4)
            )
        strand.bot_forward(call_bot)
        assert neuron1.i == 4
        assert neuron2.i == 4

    def test_call_func_with_baseproc(self):
        neuron1 = NeuronTest()
        neuron2 = NeuronTest()
        neuron2.i = 5
        strand = neuron1 >> neuron2
        call_bot = bot.Call(
            'get'
            )
        strand.bot_forward(call_bot)
        results = call_bot.report()
        assert results[neuron1] == 1
        assert results[neuron2] == 5

    def test_call_func_with_proc(self):
        neuron1 = NeuronTest()
        neuron2 = NeuronTest()
        neuron2.i = 5
        strand = neuron1 >> neuron2
        call_bot = bot.Call(
            'get', process=lambda x: x - 5
            )
        strand.bot_forward(call_bot)
        results = call_bot.report()
        assert results[neuron1] == -4, (
            'Neuron1 should be 1 - 5 = -4'
            )
        assert results[neuron2] == 0, (
            'Neuron1 should be 5 - 5 = 0'
            )

