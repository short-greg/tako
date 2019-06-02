import pytest
import tako


# @pytest.mark.incremental
class TestNeuron(object):
    def test_neuron_initialization(self):
        neuron = tako.Neuron()
    
    def test_neuron_concatenation(self):
        strand = tako.Neuron() >> tako.Neuron()
        assert type(strand) == tako.Strand
    
    
    def test_that_cannot_self_concatenate(self):
        """
        Ensure that
        """
        """
        neuron = tako__.Neuron()
        strand = neuron >> neuron
        assert type(strand) == tako__.Strand
        """
        pass
    
    def test_forward_causes_not_implemented(self):
        neuron = tako.Neuron()
        with pytest.raises(NotImplementedError):
            neuron(1)
    
    def test_spawn(self):
        neuron = tako.Neuron().spawn()
        assert type(neuron) == tako.Neuron
    

class TestNoop(object):
    
    def test_forward_does_not_change_value(self):
        neuron = tako.Noop()
        assert neuron.forward(1) == 1, (
            'The value should not change with a Noop nerve.'
        )
    
    def test_forward_does_not_change_value_with_strand(self):
        strand = tako.Noop() >> tako.Noop()
        assert strand(1) == 1, (
            'The value should not change with a Noop nerve.'
        )
    
    def test_spawn(self):
        neuron = tako.Noop().spawn()
        assert type(neuron) == tako.Noop


class TestOpNeuron(object):
    
    def test_forward_updates_value(self):
        def op(x):
            return x + 1
        
        neuron = tako.OpNeuron(op)
        assert neuron.forward(1) == 2, (
            'The value should become 2.'
        )
    
    def test_forward_with_strand(self):
        def op(x):
            return x + 1

        strand = tako.OpNeuron(op) >> tako.OpNeuron(op)
        assert strand(1) == 3, (
            'The value should not change with a Noop nerve.'
        )
    
    def test_spawn(self):
        def op(x):
            return x + 1
        neuron = tako.OpNeuron(op).spawn()
        assert neuron.forward(1) == 2, (
            'The value should become 2.'
        )


class TestArg(object):
    
    def test_arg_creation_with_0(self):
        
        arg = tako.arg[0]
        assert arg.key == 0, (
            'The key for the arg should be 0.'
        )
    
    def test_arg_creation_with_key(self):
        
        arg = tako.arg.x
        assert arg.key == 'x', (
            'The key for the arg should be "x".'
        )


class TestDeclaration(object):
    
    def test_stem_creation_with_no_args(self):
        def op(x):
            return x + 1

        decl = tako.decl(tako.OpNeuron, op)
        neuron = decl.define(1)

        assert neuron.forward(1) == 2, (
            'The value should become 2.'
        )
    
    def test_declaration_that_is_encapsulated(self):
        def op(x):
            return x + 1

        strand = (tako.in_ >> tako.decl(tako.OpNeuron, op)).encapsulate()
        result = strand(1)

        assert result == 2, (
            'The value should become 2.'
        )

    def test_declaration_has_been_defined(self):
        def op(x):
            return x + 1

        strand = (tako.in_ >> tako.decl(tako.OpNeuron, op)).encapsulate()
        strand(1)
        result = strand(1)

        assert result == 2, (
            'The value should become 2.'
        )
        assert type(strand.lhs.outgoing) == tako.OpNeuron

    def test_declaration_has_been_defined_with_kwargs(self):
        def op(x):
            return x + 1

        strand = (tako.in_ >> tako.decl(tako.OpNeuron, op=op)).encapsulate()
        strand(1)
        result = strand(1)

        assert result == 2, (
            'The value should become 2.'
        )
        assert type(strand.lhs.outgoing) == tako.OpNeuron

    def test_declaration_with_dynamic(self):
        def op(x):
            return x + 1

        strand = (tako.in_ >> tako.Declaration(tako.OpNeuron, [op], dynamic=True)).encapsulate()
        strand(1)
        result = strand(1)

        assert result == 2, (
            'The value should become 2.'
        )
        assert type(strand.lhs.outgoing) == tako.Declaration


class TestStem(object):
    
    def test_stem_creation_with_no_args(self):
        def op(x):
            return x + 1

        stem = tako.Stem(tako.OpNeuron, op)
        neuron = stem()

        assert neuron.forward(1) == 2, (
            'The value should become 2.'
        )

    def test_stem_creation_with_index_arg(self):
        def op(x):
            return x + 1

        stem = tako.Stem(tako.OpNeuron, tako.arg[0])
        neuron = stem(op)

        assert neuron.forward(1) == 2, (
            'The value should become 2.'
        )

    def test_stem_creation_with_key_arg(self):
        def op(x):
            return x + 1

        stem = tako.Stem(tako.OpNeuron, tako.arg.k)
        neuron = stem(k=op)

        assert neuron.forward(1) == 2, (
            'The value should become 2.'
        )


class TestEmit(object):
    
    def test_emit_with_no_input(self):
        emit = tako.Emit(1)
        assert emit() == 1, (
            'The output of emit should be 1'
        )

    def test_emit_with_input(self):
        emit = tako.Emit(1)
        with pytest.raises(AssertionError):
            emit(1)

    def test_emit_with_strand(self):
        strand = (tako.nil_ >> tako.Emit(1)).encapsulate()
        assert strand() == 1, (
            'The output of the strand should be 1.'
        )


class TestArm(object):
    
    def test_convert_strand_to_arm(self):
        arm = (tako.in_ >> (lambda x: x + 1)).arm()
        assert arm(0) == 1, (
            'The output of emit should be 1'
        )

    def test_convert_arm_to_strand(self):
        def f(x):
            return x + 1
        strand = (tako.in_ >> f).arm().strand
        assert strand(0) == 1, (
            'The output of emit should be 1'
        )


class TestTako(object):
    
    def test_use_arm_in_class(self):
        class _T(tako.Tako):
            s = tako.in_ >> (lambda x: x + 1)
        
        t = _T()
        assert t.s(1) == 2, (
            'The output of s should be 2'
        )

    def test_use_arm_in_super_class(self):
        class _T(tako.Tako):
            s = tako.in_ >> (lambda x: x + 1)
        
        class _S(_T):
            pass
        
        s = _S()
        assert s.s(1) == 2, (
            'The output of s should be 2'
        )
