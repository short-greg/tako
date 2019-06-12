import tako
from tako import flow
import pytest
from tako import bot
from tako import ref


class TestDelay(object):
    def test_delay_initialization(self):
        delay = flow.Delay(1)

    def test_delay_1(self):
        """
        Ensure that
        """
        delay = flow.Delay(1, default=0)
        assert delay(1) == 0
        assert delay(2) == 1

    def test_delay_2(self):
        """
        Ensure that
        """
        delay = flow.Delay(2, default=0)
        assert delay(1) == 0
        assert delay(2) == 0
        assert delay(3) == 1


class TestDiverge(object):
    def test_flow_initialization(self):
        diverge = flow.Diverge(
            [
                tako.Noop(),
                flow.Delay(1)
            ]
        )
    
    def test_flow_with_two_streams(self):
        diverge = flow.Diverge(
            [ 
                tako.Noop(),
                flow.Delay(1, default=0)
            ],
        )
        assert diverge([1, 1]) == (
            [1, 0]
        )
        assert diverge([2, 2]) == (
            [2, 1]
        )
    
    def test_flow_with_two_streams_using_n(self):
        diverge = flow.Diverge(
            [],
            2
        )
        assert diverge([3, 1]) == (
            [3, 1]
        )


class TestGate(object):
    
    def test_gate_initialization(self):
        flow.Gate(
            cond=lambda x: x == 1, 
            neuron=lambda x: x + 2,
            pass_on=True
        )
    
    def test_gate_with_1_value(self):
        gate = flow.Gate(
            cond=lambda x: x == 1, 
            neuron=lambda x: x + 2,
            pass_on=False
        )
        assert gate([0, 1]) == (
            (True, 3)
        )
    
    def test_gate_with_fail(self):
        gate = flow.Gate(
            cond=lambda x: x == 1, 
            neuron=lambda x: x + 2,
            pass_on=False
        )
        assert gate([1, 1]) == (
            (False, None)
        )


class TestMulti(object):
    
    def test_multi_initialization(self):
        flow.Multi(
            [      
                lambda x: x + 1,
                lambda x: x + 2
            ]
        )
    
    def test_multi_with_two(self):
        multi = flow.Multi(
            [     
                lambda x: x + 1,
                lambda x: x + 2
            ]
        )
        assert multi(1) == (
            [2, 3]
        )
    
    def test_multi_with_two_n(self):
        multi = flow.Multi(
            [
                lambda x: x + 1
            ],
            2
        )
        assert multi(1) == (
            [2, 1]
        )

    def test_multi_with_incompatible_n(self):
        with pytest.raises(AssertionError):
            flow.Multi(
                [
                    lambda x: x + 1,
                    lambda x: x + 1,
                    lambda x: x + 1
                ],
                1,
            )


class TestSwitch(object):
    
    def test_switch_initialization(self):
        flow.Switch(
            lambda x: x,
            {
                0: lambda x: x + 1,
                1: lambda x: x + 2,
            },
            default=lambda x: 0
        )
    
    def test_switch_to_first(self):
        switch = flow.Switch(
            lambda x: x,
            {
                0: lambda x: x + 1,
                1: lambda x: x + 2,       
            },
            default=lambda x: 0
        )
        assert switch((0, 2)) == (
            (0, 3)
        )
    
    def test_switch_to_default(self):
        switch = flow.Switch(
            lambda x: x,
            {
                0: lambda x: x + 1,
                1: lambda x: x + 2,
            },
            default=lambda x: 0
        )
        # default path
        assert switch((3, 2)) == (
            (3, 0)
        )


class TestCases(object):
    
    def test_switch_initialization(self):
        flow.Cases(
            [
                flow.Gate(cond=lambda x: True, neuron=lambda x: x - 1)
            ],
            default=lambda x: 0
        )

    def test_switch_test_first(self):
        cases = flow.Cases(
            [
                flow.Gate(cond=lambda x: True, neuron=lambda x: x - 1),
            ],
            default=lambda x: 0
        )
        assert cases((1, 4)) == (
            ((0, 3))
        )
    
    def test_switch_test_else(self):
        cases = flow.Cases(
            [
                flow.Gate(cond=lambda x: False, neuron=lambda x: x - 1),
            ],
            default=lambda x: 0
        )
        assert cases((1, 4)) == (
            ((flow.Cases.DEFAULT_PATH, 0))
        )


class TestOnto(object):
    
    def test_onto_initialization(self):
        flow.Onto(
            tako.Emit(1)
        )

    def test_onto_output_with_one(self):
        
        onto = flow.Onto(
            tako.nil_ >> tako.Emit(1)
        )
        assert onto(2) == (
            [2, 1]
        )
    
    def test_onto_output_with_two(self):
        
        onto = flow.Onto(
            tako.nil_ >> tako.Emit(1),
            tako.nil_ >> tako.Emit(2)
        )
        assert onto(2) == (
            [2, 1, 2]
        )


class TestUnder(object):
    
    def test_under_initialization(self):
        flow.Under(
            tako.Emit(1)
        )

    def test_under_output_with_one(self):  
        under = flow.Under(
            tako.nil_ >> tako.Emit(1)
        )
        assert under(2) == (
            [1, 2]
        )

    def test_under_output_with_two(self):
        
        under = flow.Under(
            tako.nil_ >> tako.Emit(1),
            tako.nil_ >> tako.Emit(2)
        )
        assert under(2) == (
            [1, 2, 2]
        )


class TestStore(object):
    
    def test_store_init(self):
        flow.Store(lambda x: x + 1)

    def test_store_lambda_output(self):
        lam = flow.Store(lambda x: x + 1)
        lam(2)
        assert lam.output == 3, (
            'Should have stored the value 3 ' + 
            'for the output'
        )

    def test_store_lambda_output_default(self):
        lam = flow.Store(lambda x: x + 1, default=4)
        assert lam.output == 4, (
            'THe output should be the default output'
        )

    def test_store_lambda_output_reset(self):
        lam = flow.Store(lambda x: x + 1, default=4)
        lam(4)
        lam.reset()
        assert lam.output == 4, (
            'THe output should be the default output'
        )

class TestBotInform(object):
    
    def test_botinform_init(self):
        flow.BotInform(lambda x: x + 1, name='hi')

    def test_store_lambda_output(self):
        lam = flow.BotInform(lambda x: x + 1)
        ware = tako.Warehouse()
        lam(2, ware)
        assert ware.probe(lam.key) == (3, True), (
            'Warehouse have stored the value 3 ' + 
            'for the output'
        )

    def test_store_lambda_no_use_neuron_key(self):
        lam = flow.BotInform(lambda x: x + 1, name='XX', use_neuron_key=False)
        ware = tako.Warehouse()
        lam(2, ware)
        
        assert ware.probe(lam.key) == (3, True), (
            'Warehouse have stored the value 3 ' + 
            'for the output'
        )


class TestBotProbe(object):
    
    def test_botinform_init(self):
        lam = flow.BotInform(lambda x: x + 1)
        flow.BotProbe(lam, name='hi')

    def test_probe_lambda_output(self):
        lam = flow.BotInform(lambda x: x + 1)
        probe = flow.BotProbe(lam)
        ware = tako.Warehouse()
        lam(2, ware)
        assert probe(None, ware) == 3, (
            'Warehouse have stored the value 3 ' + 
            'for the output'
        )

    def test_probe_lambda_output_with_ref(self):
        lam = flow.BotInform(lambda x: x + 1)
        probe = flow.BotProbe(ref.ref(lam))
        ware = tako.Warehouse()
        lam(2, ware)
        assert probe(None, ware) == 3, (
            'Warehouse have stored the value 3 ' + 
            'for the output'
        )

    def test_probe_lambda_output_with_name(self):
        lam = flow.BotInform(lambda x: x + 1, name='T', use_neuron_key=False)
        probe = flow.BotProbe(name='T')
        ware = tako.Warehouse()
        lam(2, ware)
        assert probe(None, ware) == 3, (
            'Warehouse have stored the value 3 ' + 
            'for the output'
        )
