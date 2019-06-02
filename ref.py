import __init__ as tako
from __init__ import to_neuron



"""
--- References are nerves that perform an evaluation
-- on a table or function
-- 
-- There are 4 basic kinds of references
-- They can be created via placeholder as defined in the
-- placeholder class.  An example is 
-- OutputFunction() .. oc.input(oc.my.x, oc.my.y)
-- 
-- Types:
-- Input: Does an evaluation on the input that
-- is passed in from the preceding nerve.
-- My: Does an evaluation on the owner of the nerve
-- (the tako__ or table instance that the nerve belongs to)
-- Val: Does an evaluation on a value that is passed
-- into the nerve on construction
-- Ref : refers to a value that is passed in upon
-- initialization.
-- On top of that a NerveRef can be created using
-- oc.r(oc.Ref or placeholder) 
-- The nerve refs make the references accessible just
-- like other nerves.
"""

class Attr(object):
    
    def __init__(self, key):
        self._key = key
        
    def get(self, obj):
        
        return object.__getattribute__(obj, self._key)


class Idx(object):
    
    def __init__(self, key):
        self._key = key

    def get(self, obj):
        return obj[self._key]


class RefBase(tako.Neuron):
    """
    --- @abstract
    -- Base nerve for all value references 
    -- (i.e. references to items other than arms)
    """
    def __init__(self, path):
        """
        --- @constructor
        -- @param path - path to access the value 
        -- {string} or strings
        """
        super().__init__()
        self._path = path or []
        self._base_val = None

    @staticmethod
    def _get_val(path, val, x):
        print(path, val, x)
        prev_val = val
        for p in path:
            if type(p) == InCall:
                val = p([prev_val, x])
            else:
                val = p.get(prev_val)
            prev_val = val
        return val
  
    def __call__(self, x, bot=None):
        path = self._path
        
        if type(path) == str:
            val = self._base_val[path]
        else:
            val = self._get_val(path, self._base_val, x)
        
        return val


class EmissionRef(RefBase):
    def __call__(self, x, bot=None):
        self._base_val = x
        return super().__call__(x, bot)


class Child(object):
    def __init__(self):
        self._super = None
    
    def set_super(self, super_):
        if self._super is None:
            self._super = super_
            return True
        else:
            return False


class Owned(object):
    def __init__(self):
        self._owner = None
    
    def set_owner(self, owner):
        if self._owner is None:
            self._owner = owner
            return True
        else:
            return False

"""
y >> x >> Onto(my.z)

z = 
y = 

nn.Linear(2, 2) >> oc.BotStore('<name>')
oc.Emit(my.z)

Diverge(
 In_ >> y, 
 Nil_ >> z
)
"""


class MyRef(RefBase, Owned):
    """
    --- The base class for all references
    -- @input Can be anything
    -- @output whatever the evaluation of the reference
    -- spits out
    """
    def __init__(self, path):
        super().__init__(path)
        self._owner = None
    
    def set_owner(self, owner):
        if Owned.set_owner(self, owner):
            print('Setting owner')
            self._base_val = owner
            for p in self._path:
                if isinstance(p, InCall):
                    p.set_owner(owner)
            return True
        return False


class SuperRef(RefBase):
    def __init__(self, path):
        super().__init__(path)
        self._super = None

    def set_super(self, super_):
        if self._super is None:
            self._base_val = super_
            for p in self._path:
                if isinstance(p, InCall):
                    p.set_super(super_)
            return True
        return False


class ValRef(RefBase):
    
    def __init__(self, val, path, args=None):
        """
        --- @param val - the val to 
        -- @param path - path to access the value 
        -- {string} or string
        -- @param args - Args to pass if a function  {} or nil
        -- (if args is nil will not call)
        """
        args = args or []
        super().__init__(path)
        self._base_val = val
    
    def update_val(self, val):
        self._val = val


class NeuronRef(tako.Neuron, Owned, Child):
    def __init__(self, ref):
        super().__init__()
        self._ref = tako.to_neuron(ref)
        # self._to_probe = True
    
    @property
    def ref_key(self, x=None):
        return self._ref(x).key
    
    def __call__(self, x, bot=None):
        neuron = self.get_ref(x)
        return neuron(x, bot)
    
    def get_ref(self, x=None):
        return self._ref(x)

    def bot_forward(self):
        return [self._ref]


# TODO: Want to wrap ValRef with Emit... Emit(ValRef)  
def r(ref):
    return NeuronRef(ref)

"""
class Idx(object):
    def __init__(self, key):
        self._key = key
        
    def __exec__(self, x):
        return x.__getitem__(self._key)


class Attribute(object):
    
    def __init__(self, key):
        self._key = key
        
    def forward(self, x):
        if type(x) == 'type':
            return x.__getattribute__(x, self._key)
        else:
            return x.__getattribute__(self._key)
"""


class InCall(tako.Neuron, Owned, Child):
    """
    --- Object to call a function that exists
    -- within a reference.
    -- 
    -- @input {function, input, [object]}
    -- input is the input into the ref
    -- object is the object that contains the function
    -- to use if a selfCall
    -- @output The output of the function
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        Owned.__init__(self)
        Child.__init__(self)
        self._args = [self._prepare_arg(arg) for arg in args]
        self._kwargs = {k: self._prepare_arg(arg) for k, arg in kwargs}
        # not sure if i need this????
        # it appears i do not need this
        # self._instance_method = instance_method

    @staticmethod
    def _prepare_arg(arg):
        if isinstance(arg, Placeholder) or is_refmeta(arg):
            return tako.to_neuron(arg)
        else:
            return arg
    
    @staticmethod
    def _output_arg(arg, x):
        if isinstance(arg, RefBase):
            return arg(x[1])
        else:
            return arg

    def __call__(self, x, bot=None):
        """
        @param input[0] - function to call
        @param input[1] - input
        """
        args_output = [self._output_arg(arg, x) for arg in self._args]
        kwargs_output = {k: self._output_arg(arg, x) for k, arg in self._kwargs.items()}
        return x[0](*args_output, **kwargs_output)

    def set_super(self, super_):
        def _set_arg_super(arg):
            if isinstance(arg, Child):
                arg.set_super(super_)
        
        if Child.set_super(self, super_):
            _ = [_set_arg_super(arg) for arg in self._args]
            _ = [_set_arg_super(arg) for k, arg in self._kwargs.items()]
        else:
            return False
    
    def set_owner(self, owner):
        def _set_arg_owner(arg):
            if isinstance(arg, Owned):
                arg.set_owner(owner)
        if Owned.set_owner(self, owner):
            _ = [_set_arg_owner(arg) for arg in self._args]
            _ = [_set_arg_owner(arg) for k, arg in self._kwargs.items()]
        else:
            return False


class Call(InCall):
    """
    --- Calls a member method
    -- In a sense it combines 'InCall' and 'Emit'
    -- @input {function, input, [object]}
    -- input is the input into the ref
    -- object is the object that contains the function
    -- to use if a selfCall
    -- @output The output of the function
    """

    def __init__(self, f, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._f = f

    def __call__(self, x, bot=None):
        """
        @param input[0] - function to call
        @param input[1] - input
        """
        return super().__call__((self._f, x), bot)


"""
--- Placeholders are nerves used for convenience to
-- create references to other nerves, functions 
-- and data within the strand definition.
-- 
-- 
-- There are four basic types of placeholders
-- 
-- oc.input - Creates an input reference 
-- (the input into the nere)
--
-- oc.my - Creates a reference to the 
-- owner of the nerve (the Tako
-- or some other table/object) to 
-- access data within it
--
-- oc.super - Creates a reference to the 
-- super class/tako__ of the nerve
-- in order to call its 
-- oc.ref(value) - Creates a reference to the 
-- value that gets passed in
--
-- oc.r(oc.Ref) -> creates an NerveRef so that
-- the reference will be treated like
-- a nerve (will call inform, probe, informGrad
-- etc)
--
-- @usage - y = oc.r(oc.my.x) 
-- oc.r() creates an arm reference to 
-- the member x of self
-- @usage - nn.Linear(2, 2)
-- @usage oc.ref{y=1}.y <- will create a placeholder
--            referring to the table {y=1} and 
-- 
-- You can create arm/nerve references for my, 
-- super, and ref.
-- This is used for 'essentially' having multiple inputs
-- into a nerve.  There is no arm reference for input however
-- since input is the value that gets passed into the arm 
-- (as of now).
"""


class Placeholder(object):
    """
    --- @abstract
    -- 
    -- Base class for Plachoelders
    --
    -- Used for declaring where a reference will
    -- point.  Placholders are used in place
    -- of actual Reference nerves for ease of use.
    --
    -- Concatenating a placholder with a nerve
    -- will implicitly convert it to a Reference
    -- nerve.
    --
    -- nn.Linear(2, 2) .. oc.my.x
    -- Will create a strand with an oc.MyRef at the
    -- end of the strand.
    --
    -- Calling a placeholder will create a function
    -- call in the reference Call.  Placeholders can
    -- be passed into the function call.
    --
    -- oc.my.x(oc.input) -> will call the function 
    --   x with the input that was passed into the
    --   
    -- oc.my:x(oc.input) -> will call the function 
    -- x with the input that was passed into the
    -- nerve as the second argument and x as
    -- the first argument.
    --
    -- oc.my.x(oc.input).y -> will pass the input into
    -- the function x and then return the value
    -- at key y in the index.
    """

    def __init__(self):
        """
        --- @constructor 
        -- @param refType - Whether a global
        -- @param params.args - Arguments to a function call
        -- @param params.index - Index to access from reference
        -- @param params.reference - Reference to the item
        -- if DEFINED
        -- @param params._refType 
        """
        self.__refindex__ = []

    def __str__(self):
        return 'Placeholder: %s ' % type(self)

    def __getitem__(self, key):
        self.__refindex__.append(
            Idx(key)
        )
        return self
    
    def __getattr__(self, key):
        self.__refindex__.append(
            Attr(key)
        )
        return self
        
    def __call__(self, *args, **kwargs):
        self.__refindex__.append(
            InCall(*args, **kwargs)
        )
        return self

    @classmethod
    def __refmeta__(cls):
        raise NotImplementedError
    
    def __neuron__(self):
        raise NotImplementedError 

    """
        if not oc.isInstance(self) then
          rawset(self, index, val)
        end
      end
    """

Placeholder.__rshift__ = tako.Neuron.__rshift__


class EmissionPlaceholder(Placeholder):
    """
    --- References the input that is passed into the
    -- nerve.
    --
    -- oc.input(1) <- will pass 1 into the function
    -- that gets passed into the nerve as an input.
    --
    -- oc.ref(x)(oc.input) will pass the input
    -- into the function x as an argument.
    """
    def __neuron__(self):
        return EmissionRef(self.__refindex__)
    
    def __refmeta__(self):
        return emission


class MyPlaceholder(Placeholder):
    """
    --- References the object that the nerve
    -- belongs to.  Possibly a Tako
    --
    -- @usage oc.my:y(oc.input, oc.my.x) will
    -- call the Tako's function 'y' and 
    -- pass in y as the first argument, the
    -- input as the second argument
    -- and Tako's member 'x' as the third.
    """
    def __neuron__(self):
        return MyRef(self.__refindex__)

    def __refmeta__(self):
        return my


class ValPlaceholder(Placeholder):
    """
    --- Used for referencing an arbitrary value.
    --
    -- @usage t = {1, 2, 3}
    -- oc.ref(t)[1] will output 1
    -- oc.ref(1) will also output 1
    """
    
    def __init__(self, val):
        """
          --- @constructor 
          -- @param val - The value to access
        """
        super().__init__()
        self.__ref__ = val

    def __neuron__(self):
        return ValRef(
            self.__ref__, self.__refindex__
        )

    def __refmeta__(self):
        return ref


class SuperPlaceholder(Placeholder):
    
    def __neuron__(self):
        return SuperRef(self.__refindex__)
    
    def __refmeta__(self):
        return super_


class _Refmeta(object):
    
    def __init__(self, refmeta_type, args=None):
        self._refmeta_type = refmeta_type
        self._args = args or []
    
    def __call__(self, *args, **kwargs):
        return self._refmeta_type(*self._args)(*args, **kwargs)
    
    def __getattr__(self, key):
        return self._refmeta_type(*self._args).__getattr__(key)
    
    def __getitem__(self, key):
        return self._refmeta_type(*self._args).__getitem__(key)
    
    def __neuron__(self):
        return to_neuron(self._refmeta_type(*self._args))


class _Valrefmeta(_Refmeta):
    
    def __init__(self, val):
        super().__init__(ValPlaceholder, [val])


my = _Refmeta(MyPlaceholder)
emission = _Refmeta(EmissionPlaceholder)
super_ = _Refmeta(SuperPlaceholder)

def ref(val):
    return _Valrefmeta(val)



def is_refmeta(val):
    return isinstance(val, _Refmeta)
