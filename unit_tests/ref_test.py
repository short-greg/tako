import ref
from __init__ import to_neuron
import __init__ as tako


class TestEmissionRef(object):

    def test_emission_ref_creation(self):
        to_neuron(ref.emission)
    
    def test_emission_ref_creation_with_member(self):
        to_neuron(ref.emission.x)
        
    def test_emission_ref_creation_with_attr(self):
        to_neuron(ref.emission[0])

    def test_emission_ref_execution_with_getitem(self):
        strand = tako.in_ >> ref.emission[2]
        assert strand([0, 1, 2]) == 2

    def test_emission_ref_execution_with_getattr(self):
        class T(object):
            f = 2
            g = 3
        
        strand = tako.in_ >> ref.emission.f
        assert strand(T) == 2
    
    def test_emission_ref_execution_with_neuron(self):
        def v(x):
            return 2
        
        class T(object):
            f = to_neuron(v)
        
        strand = tako.in_ >> ref.r(ref.emission.f)
        assert strand(T) == 2


class TestMyRef(object):

    def test_my_ref_creation(self):
        to_neuron(ref.my)

    def test_my_ref_creation_with_member(self):
        to_neuron(ref.my.x)
        
    def test_my_ref_creation_with_attr(self):
        to_neuron(ref.my[0])

    def test_my_ref_execution_with_attr(self):
        class T:
            j = 1
        
        r = to_neuron(ref.my.j)
        r.set_owner(T)
        
        strand = tako.nil_ >> r
        assert strand() == 1


class TestSuperRef(object):

    def test_my_ref_creation(self):
        to_neuron(ref.super_)

    def test_my_ref_creation_with_member(self):
        to_neuron(ref.super_.x)
        
    def test_my_ref_creation_with_attr(self):
        to_neuron(ref.super_[0])

    def test_my_ref_execution_with_attr(self):
        class T:
            j = 1
        
        class V(T):
            pass
        
        r = to_neuron(ref.super_.j)
        r.set_super(T)
        
        strand = tako.nil_ >> r
        assert strand() == 1


class TestValRef(object):

    def test_my_ref_creation(self):
        to_neuron(ref.ref)

    def test_my_ref_creation_with_member(self):
        j = [0]
        to_neuron(ref.ref(j)[0])

    def test_my_ref_creation_with_attr(self):
        class V:
            f = 1
        to_neuron(ref.ref(V).f)

    def test_my_ref_execution_with_attr(self):
        class V:
            f = 1
        
        r = to_neuron(ref.ref(V).f)
        
        strand = tako.nil_ >> r
        assert strand() == 1
    
    def test_my_ref_execution_with_call(self):
        class V:
            def f(self):  
                return 1
        
        t = V()
        r = to_neuron(ref.ref(t).f())
        
        strand = tako.nil_ >> r
        assert strand() == 1
    
    def test_my_ref_execution_with_two_calls(self):
        class X:
            def p(self):
                return 1
        
        class V:
            def f(self):  
                return X()
        
        t = V()
        r = to_neuron(ref.ref(t).f().p())
        
        strand = tako.nil_ >> r
        assert strand() == 1


class TestCall(object):

    def test_call_creation(self):
        to_neuron(ref.Call('a'))
    
    def test_call_execution(self):
        def y(a):
            return a + '_a'

        r = ref.Call(y, 'a')
        
        strand = tako.in_ >> r
        assert strand() == 'a_a'

    def test_call_execution_with_ref(self):
        def y(a, b):
            return a + b
        
        class Z:
            def z(self):
                return '_a'

        class J:
            a = 'a'
        
        r = ref.Call(y, ref.emission.a, ref.my.z())
        r.set_owner(Z())
        
        strand = tako.in_ >> r
        assert strand(J) == 'a_a'


"""
    def test_my_ref_execution_with_neuron(self):
        def v():
            return 2
        
        class T(object):
            f = to_neuron(v)

        r = to_neuron(ref.my.j)
        r.set_owner(T)
        
        strand = tako.nil_ >> ref.r(ref.my.f)
        assert strand() == 2
    """
