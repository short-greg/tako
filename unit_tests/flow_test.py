import __init__ as tako
import flow
import pytest


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
            None, 
            tako.Noop(),
            flow.Delay(1)
        )
    
    def test_flow_with_two_streams(self):
        diverge = flow.Diverge(
            None, 
            tako.Noop(),
            flow.Delay(1, default=0)
        )
        assert diverge([1, 1]) == (
            [1, 0]
        )
        assert diverge([2, 2]) == (
            [2, 1]
        )
    
    def test_flow_with_two_streams_using_n(self):
        diverge = flow.Diverge(
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
            [True, 3]
        )
    
    def test_gate_with_fail(self):
        gate = flow.Gate(
            cond=lambda x: x == 1, 
            neuron=lambda x: x + 2,
            pass_on=False
        )
        assert gate([1, 1]) == (
            [False, None]
        )


class TestMulti(object):
    
    def test_multi_initialization(self):
        flow.Multi(
            None,
            lambda x: x + 1,
            lambda x: x + 2
        )
    
    def test_multi_with_two(self):
        multi = flow.Multi(
            None,
            lambda x: x + 1,
            lambda x: x + 2
        )
        assert multi(1) == (
            [2, 3]
        )
    
    def test_multi_with_two_n(self):
        multi = flow.Multi(
            2,
            lambda x: x + 1
        )
        assert multi(1) == (
            [2, 1]
        )

    def test_multi_with_incompatible_n(self):
        with pytest.raises(AssertionError):
            flow.Multi(
                1,
                lambda x: x + 1,
                lambda x: x + 1,
                lambda x: x + 1
            )


class TestSwitch(object):
    
    def test_switch_initialization(self):
        flow.Switch(
            lambda x: x,
            lambda x: x + 1,
            lambda x: x + 2,
            default=lambda x: 0
        )
    
    def test_switch_to_first(self):
        switch = flow.Switch(
            lambda x: x,
            lambda x: x + 1,
            lambda x: x + 2,
            default=lambda x: 0
        )
        assert switch((0, 2)) == (
            (0, 3)
        )
    
    def test_switch_to_default(self):
        switch = flow.Switch(
            lambda x: x,
            lambda x: x + 1,
            lambda x: x + 2,
            default=lambda x: 0
        )
        # default path
        assert switch((3, 2)) == (
            (3, 0)
        )


class TestCases(object):
    
    def test_switch_initialization(self):
        flow.Cases(
            flow.Gate(cond=lambda x: True, neuron=lambda x: x - 1),
            else_=lambda x: 0
        )

    def test_switch_test_first(self):
        cases = flow.Cases(
            flow.Gate(cond=lambda x: True, neuron=lambda x: x - 1),
            else_=lambda x: 0
        )
        assert cases((1, 4)) == (
            ((0, 3))
        )
    
    def test_switch_test_else(self):
        cases = flow.Cases(
            flow.Gate(cond=lambda x: False, neuron=lambda x: x - 1),
            else_=lambda x: 0
        )
        assert cases((1, 4)) == (
            (('Else', 0))
        )


class TestOnto(object):
    
    def test_onto_initialization(self):
        flow.Onto(
            tako.Emit(1)
        )

    def test_onto_output_with_one(self):
        
        onto = flow.Onto(
            tako.Nil_() >> tako.Emit(1)
        )
        assert onto(2) == (
            [2, 1]
        )
    
    def test_onto_output_with_two(self):
        
        onto = flow.Onto(
            tako.Nil_() >> tako.Emit(1),
            tako.Nil_() >> tako.Emit(2)
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
            tako.Nil_() >> tako.Emit(1)
        )
        assert under(2) == (
            [1, 2]
        )

    def test_under_output_with_two(self):
        
        under = flow.Under(
            tako.Nil_() >> tako.Emit(1),
            tako.Nil_() >> tako.Emit(2)
        )
        assert under(2) == (
            [1, 2, 2]
        )
