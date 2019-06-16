from tako import iterator
import tako



class TestAccessor(object):
    
    def test_initialization(self):
        iterator.Accessor([1, 2, 3])

    def test_to_iter(self):
        iter_ = iterator.Accessor([1, 2, 3]).to_iter()
        assert type(iter_) == iterator.Iter

    def test_len(self):
        acc = iterator.Accessor([1, 2, 3])
        assert len(acc) == 3
    
    def test_getitem(self):
        acc = iterator.Accessor([1, 2, 3])
        assert acc[0] == 1

    def test_to_iter_spawn(self):
        iter_ = iterator.Accessor([1, 2, 3]).spawn().to_iter()
        assert type(iter_) == iterator.Iter


class TestShuffle(object):
    
    def test_initialization(self):
        meta = iterator.Shuffle()
        acc = iterator.Accessor([1, 2, 3])
        acc.wrap(meta)

    def test_len(self):
        meta = iterator.Shuffle()
        acc = iterator.Accessor([1, 2, 3])
        acc.wrap(meta)
        assert len(acc) == 3

    def test_getitem(self):
        meta = iterator.Shuffle()
        acc = iterator.Accessor([1, 2, 3])
        acc.wrap(meta)
        assert acc[0] in {1, 2, 3}

    def test_to_iter_spawn(self):
        iter_ = iterator.Accessor([1, 2, 3]).spawn().to_iter()
        assert type(iter_) == iterator.Iter

    def test_spawn_with_len(self):
        meta = iterator.Shuffle().spawn()
        acc = iterator.Accessor([1, 2, 3])
        acc.wrap(meta)
        assert len(acc) == 3

class TestBatch(object):
    
    def test_initialization(self):
        meta = iterator.Batch(size=2)
        acc = iterator.Accessor([1, 2, 3, 4, 5])
        acc.wrap(meta)

    def test_len(self):
        meta = iterator.Batch(size=2)
        acc = iterator.Accessor([1, 2, 3, 4, 5])
        acc.wrap(meta)
        assert len(acc) == 3

    def test_spawn_with_len(self):
        meta = iterator.Batch(size=2)
        acc = iterator.Accessor([1, 2, 3, 4, 5])
        acc.wrap(meta.spawn())
        assert len(acc) == 3

    def test_getitem(self):
        meta = iterator.Batch(size=2)
        acc = iterator.Accessor([1, 2, 3, 4, 5])
        acc.wrap(meta)
        assert acc[0] == [1, 2]
        assert acc[1] == [3, 4]
        assert acc[2] == [5]


class TestReverse(object):
    
    def test_initialization(self):
        meta = iterator.Reverse()
        acc = iterator.Accessor([1, 2, 3])
        acc.wrap(meta)

    def test_len(self):
        meta = iterator.Reverse()
        acc = iterator.Accessor([1, 2, 3])
        acc.wrap(meta)
        assert len(acc) == 3

    def test_spawn_with_len(self):
        meta = iterator.Reverse()
        acc = iterator.Accessor([1, 2, 3])
        acc.wrap(meta)
        acc = acc.spawn()
        assert len(acc) == 3

    def test_getitem(self):
        meta = iterator.Reverse()
        acc = iterator.Accessor([1, 2, 3])
        acc.wrap(meta)
        assert [acc[0], acc[1], acc[2]] == (
            [3, 2, 1]
        )

class TestToIter(object):
    
    def test_initialization(self):
        iterator.ToIter()

    def test_get(self):
        strand = (
            tako.in_ >> 
            iterator.Accessor() >> 
            iterator.ToIter()
        )
        assert strand([1, 2, 3]).get() == 1

    def test_set(self):
        strand = (
            tako.in_ >> 
            iterator.Accessor() >> 
            iterator.ToIter()
        )
        res = strand([1, 2, 3])
        assert res.get() == 1
        res.set(3)
        assert res.get() == 3

    def test_adv(self):
        strand = (
            tako.in_ >> 
            iterator.Accessor() >> 
            iterator.ToIter()
        )
        res = strand([1, 2, 3])
        res.adv()
        assert res.get() == 2

    def test_at_end(self):
        strand = (
            tako.in_ >> 
            iterator.Accessor() >> 
            iterator.ToIter()
        )
        res = strand([1, 2, 3])
        res.adv()
        res.adv()
        res.adv()
        assert res.at_end() == True

    def test_spawn_with_get(self):
        strand = (
            tako.in_ >> 
            iterator.Accessor() >> 
            iterator.ToIter()
        ).spawn()
        assert strand([1, 2, 3]).get() == 1

