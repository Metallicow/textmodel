# -*- coding: latin-1 -*-

# Neuer Stand: repariert. Sollte mehr getestet werden.
#
# Stand: es gibt noch ein konzeptionelles Problem. Das ist auch der
# Grund f�r den Fehler in test_01. Das Problem: bisher ist ungekl�rt
# ob insert(i, n) links oder rechts von Marken, die an i liegen
# eingef�gt wird.
# 
# In Writer: 
#  - Marken werden nach rechts verschoben (bei Formatierung)
# Das ist auch das Verhalten, das wir f�r Nummerierungen brauchen


# Konzepte die hier ausprobiert werden sollen:
#  - Node enth�lt n leerstellen links der Marke
#  - insert & remove �ndern die Hierarchie nicht, sondern nur Werte n
#
# Achtung: auch wenn der Code �hnlich aussieht wie texel, so gibt es
# konzeptionelle Unterschiede. Hier sind die Noden ver�nderbar! 
#  - insert / remove �ndert die Hierarchie nicht, aber die Gewichte n
#  - create_mark / remove_mark �ndert die Hierarchie auf nicht reentrent-
#    f�hige weise
#


class Mark:
    def __init__(self, label, n=0, parent=None):
        self.n = n
        self.label = label
        self.parent = None
        
    def get(self):
        if not self.parent:
            return None
        return abspos(self)+self.n

        
class Group:
    def __init__(self, childs, parent=None):
        self.childs = tuple(childs)
        self.parent = parent
        self.n = sum([c.n for c in childs])
        for c in childs:
            c.parent = self


def depth(tree):
    d = 0
    if isinstance(tree, Group):
        for child in tree.childs:
            d = max(d, depth(child))
        d += 1
    return d


def dump(tree, i0=0, d=0):
    if isinstance(tree, Mark):
        print "    "*d, i0+tree.n, tree.label
    elif isinstance(tree, Group):
        print "    "*d, i0, "Group()"
        for c in tree.childs:
            dump(c, i0, d+1)
            i0 += c.n


def get_marks(tree, i0=0):
    if isinstance(tree, Mark):
        return [(i0+tree.n, tree)]
    l = []
    for child in tree.childs:
        l.extend(get_marks(child, i0))
        i0 += child.n
    return l
    

def abspos(node):
    p = node.parent
    if p is None:
        return 0
    i = 0
    for c in p.childs:
        if c is node:
            return i+abspos(p)
        i += c.n 
    raise Exception() # bad tree structure 
    

def strip(element):
    n = element.n
    while isinstance(element, Group) and len(element.childs) == 1:
        element = element.childs[0]
    assert n == element.n
    return element
    
              
nmax = 15

# XXX can be replaced by a simpler algorith based upon the assumption
# that len(l) < 2*nmax. In other words: splitting into two groups is
# always enough.

def groups(l):
    r = []
    N = len(l)
    if N == 0:
        return r

    n = N // nmax
    if n*nmax < N:
        n = n+1
    rest = n*nmax-N

    a = nmax-float(rest)/n
    b = a
    while l:
        i = int(b+1e-10)
        r.append(Group(l[:i]))
        l = l[i:]
        b = b-i+a
    return r             

def grouped(stuff):
    while len(stuff) > nmax:
        stuff = groups(stuff)
    g = Group(stuff)
    return strip(g)


def add_mark(tree, i, m):
    if isinstance(tree, Group):
        if not tree.childs:
            m.n = i
            return [m]
        l = []
        for k, child in enumerate(tree.childs):
            l.append(child)
            i -= child.n
            if i <= 0:
                break
        l.pop()
        l.extend(add_mark(child, i+child.n, m))
        l.extend(tree.childs[k+1:])
        return groups(l)
    elif i >= tree.n:
        m.n = i-tree.n
        return [tree, m]
    else:
        m.n = i
        tree.n -= i        
        return [m, tree]


def remove_mark(tree, mark, i):
    if tree is mark:
        mark.parent = None
        return []
    if not isinstance(tree, Group):
        # XXX some assertions? tree.n == 0, what else? 
        return [tree]
    l = []
    j = i
    for child in tree.childs:
        n = child.n
        if 0 <= j <= n:
            l.extend(remove_mark(child, mark, j))
        else:
            l.append(child)
        j -= n
    g = Group(l)
    if g.n < tree.n:
        insert(g, i, tree.n-g.n)
    return [g]


def remove(tree, i1, i2):
    assert i2 >= i1 >= 0
    tree.n -= max(min(i2, tree.n) - max(i1, 0), 0)
    if isinstance(tree, Group):
        for child in tree.childs:
            j = child.n
            child.n -=  max(min(i2, j) - max(i1, 0), 0)
            i1 -= j
            i2 -= j
            if i2 <= 0:
                break
                
def insert(tree, i, n):
    if 0 <= i <= tree.n:
        tree.n += n
    if isinstance(tree, Group):
        for child in tree.childs:
            j = child.n
            if i <= j:
                insert(child, i, n)
                break
            i -= j



class MarkBuffer:
    def __init__(self):
        self.tree = Group([])

    def create_mark(self, i, label=''):
        m = Mark(label)
        self.tree = grouped(add_mark(self.tree, i, m))
        return m

    def remove_mark(self, m):
        i = m.get()
        #print "remove ", i
        self.tree = grouped(remove_mark(self.tree, m, i))

    def insert(self, i, n):
        insert(self.tree, i, n)

    def remove(self, i1, i2):
        if not 0 <= i1 <= i2:
            raise IndexError((i1, i2))
        remove(self.tree, i1, i2)

    def get_marks(self):
        return get_marks(self.tree)

    def _get_labels(self):
        return [(i, m.label) for (i, m) in self.get_marks()]

    def _dump(self):
        dump(self.tree)



class LinearBuffer:
    # For speed comparison only. Incomplete.
    def __init__(self):
        self.positions = []
        self.marks = []
        
    def create_mark(self, i, label=''):
        positions = self.positions
        marks = self.marks
        k = 0
        for k, j in enumerate(positions):
            if j >= i:
                break
        positions.insert(k, i)
        marks.insert(k, Mark(i, label))

    def insert(self, i, n): # slightly faster
        positions = self.positions
        for k in range(len(positions)):
            if positions[k] > k: 
                positions[k] += n

    def remove(self, i1, i2):
        n = i2-i1
        positions = self.positions
        for k in range(len(positions)):
            j = positions[k]
            if i1 < j:
                positions[k] = max(i1, j-n)
                



def test_00():
    "add_mark"
    b = MarkBuffer()
    A = b.create_mark(0, 'A')
    B = b.create_mark(1, 'B')
    C = b.create_mark(2, 'C')
    assert b._get_labels() == [(0, 'A'), (1, 'B'), (2, 'C')]
    assert A.get() == 0
    assert B.get() == 1
    assert C.get() == 2

    b = MarkBuffer()
    A = b.create_mark(10, 'A')
    B = b.create_mark(15, 'B')
    C = b.create_mark(5, 'C')
    #b._dump()    
    assert b._get_labels() == [(5, 'C'), (10, 'A'), (15, 'B')]

    global nmax
    nmax = 5
    for i in range(10):
        b.create_mark(i, 'X%i'%i)
    assert depth(b.tree) == 2
    #b._dump()
    assert b._get_labels() == [(0, 'X0'), (1, 'X1'), (2, 'X2'), (3, 'X3'), 
        (4, 'X4'), (5, 'C'), (5, 'X5'), (6, 'X6'), (7, 'X7'), (8, 'X8'), 
        (9, 'X9'), (10, 'A'), (15, 'B')]

    

def test_01():
    "remove_mark"
    b = MarkBuffer()
    global nmax
    nmax = 5
    #A = b.create_mark(5, 'A')
    m = []
    for i in range(6):
        m.append(b.create_mark(i, 'X%i'%i))    
    assert b._get_labels() == [(0, 'X0'), (1, 'X1'), (2, 'X2'), 
                               (3, 'X3'), (4, 'X4'), (5, 'X5')]

    for i in range(6):
        #print i, m[i].get()
        assert m[i].get() == i

    #b._dump()
    assert depth(b.tree) == 2
    b.remove_mark(m[0])
    assert m[0].parent is None
    assert m[0].get() is None

    assert m[4].get() == 4
    b.remove_mark(m[5])
    assert m[5].parent is None
    assert m[5].get() is None
    assert b._get_labels() == [(1, 'X1'), (2, 'X2'), (3, 'X3'), (4, 'X4')]


    b.remove_mark(m[3])
    assert m[3].parent is None
    assert m[3].get() is None
    #b._dump()

    #print b._get_labels()
    assert b._get_labels() == [(1, 'X1'), (2, 'X2'), (4, 'X4')]


def test_02():
    "insert"
    b = MarkBuffer()
    A = b.create_mark(10, 'A')
    B = b.create_mark(10, 'B')
    C = b.create_mark(15, 'C')

    b.insert(16, 1)
    assert b._get_labels() == [(10, 'A'), (10, 'B'), (15, 'C')]

    b.insert(15, 1)
    assert b._get_labels() == [(10, 'A'), (10, 'B'), (16, 'C')]

    b.insert(15, 1)
    assert b._get_labels() == [(10, 'A'), (10, 'B'), (17, 'C')]

    b.insert(10, 1)
    assert b._get_labels() == [(11, 'A'), (11, 'B'), (18, 'C')]


def test_03():
    "remove"
    b = MarkBuffer()
    A = b.create_mark(10, 'A')

    b.remove(9, 10)
    assert b._get_labels() == [(9, 'A')]

    b.remove(9, 11)
    assert b._get_labels() == [(9, 'A')]

    b.remove(8, 11)
    assert b._get_labels() == [(8, 'A')]

    b.remove(0, 11)
    assert b._get_labels() == [(0, 'A')]

    b = MarkBuffer()
    A = b.create_mark(10, 'A')
    B = b.create_mark(10, 'B')
    C = b.create_mark(15, 'C')

    b.remove(14, 15)
    assert b._get_labels() == [(10, 'A'), (10, 'B'), (14, 'C')]

    b.remove(13, 20)
    assert b._get_labels() == [(10, 'A'), (10, 'B'), (13, 'C')]

    b.remove(5, 20)
    assert b._get_labels() == [(5, 'A'), (5, 'B'), (5, 'C')]


def _benchmark_00(Buffer):
    from random import randrange
    b = Buffer()
    for i in range(1000):
        b.create_mark(randrange(10000))
    #b._dump()

def benchmark_00a():
    _benchmark_00(MarkBuffer)
    # 3 time slower than LinearBuffer!

def benchmark_00b():
    _benchmark_00(LinearBuffer)


def _benchmark_01(Buffer):
    from random import randrange
    b = Buffer()
    for i in range(1000):
        b.create_mark(randrange(10000))

    for i in range(10000):
        b.insert(randrange(10000), randrange(100))


def benchmark_01a():
    _benchmark_01(MarkBuffer)

def benchmark_01b():
    _benchmark_01(LinearBuffer)
    # 10x slower YES!!!


def _benchmark_02(Buffer):
    from random import randrange
    b = Buffer()
    for i in range(1000):
        b.create_mark(randrange(10000))
    for i in range(10000):
        i1 = randrange(10000)
        i2 = i1+randrange(10)
        b.remove(i1, i2)

def benchmark_02a():
    _benchmark_02(MarkBuffer)

def benchmark_02b():
    _benchmark_02(LinearBuffer)
    # 5x slower


