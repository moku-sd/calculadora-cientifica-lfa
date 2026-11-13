#!/usr/bin/env python3
"""Implementação de referência (independente do C) da mesma CFG:
   E -> E + T | E - T | T          T -> T * U | T / U | T % U | U
   U -> + U | - U | P              P -> F ^ U | F
   F -> F ! | A                    A -> NUM | CONST | f(E) | g(E,E) | (E)
Usada para (i) gerar derivação/árvore do artigo e (ii) teste diferencial contra o binário."""
import math, re

D = r'[0-9]'
NUM_RE = re.compile(r'(?:%s+(?:\.%s*)?|\.%s+)(?:[eE][+-]?%s+)?' % (D, D, D, D))
TOK = re.compile(r'\s*(?:(?P<num>' + NUM_RE.pattern + r')|(?P<id>[A-Za-z_][A-Za-z0-9_]*)|(?P<op>[-+*/%^!(),]))')

class Err(Exception): pass

def tokenize(s):
    out, i = [], 0
    while i < len(s):
        if s[i].isspace(): i += 1; continue
        m = TOK.match(s, i)
        if not m: raise Err('lex')
        i = m.end()
        if m.group('num'): out.append(('NUM', m.group('num')))
        elif m.group('id'): out.append(('ID', m.group('id')))
        else: out.append((m.group('op'), m.group('op')))
    out.append(('$', '$'))
    return out

CONSTS = {'pi': math.pi, 'e': math.e, 'tau': 2 * math.pi, 'phi': (1 + math.sqrt(5)) / 2}
F1 = ['sin','cos','tan','asin','acos','atan','sinh','cosh','tanh','sqrt','cbrt','exp','ln','log','log2','abs','floor','ceil','round']
F2 = ['max','min','atan2','hypot','pow','root']

class Parser:
    def __init__(s, toks): s.t = toks; s.i = 0
    def peek(s): return s.t[s.i][0]
    def eat(s, k=None):
        tok = s.t[s.i]
        if k and tok[0] != k: raise Err('sintaxe')
        s.i += 1; return tok
    # cada função devolve nó (nome, filhos...) ; folhas = ('tok', texto)
    def E(s):
        n = ('E', s.T())
        while s.peek() in '+-' and s.peek() != '$':
            op = s.eat(); n = ('E', n, ('tok', op[1]), s.T())
        return n
    def T(s):
        n = ('T', s.U())
        while s.peek() in ('*', '/', '%'):
            op = s.eat(); n = ('T', n, ('tok', op[1]), s.U())
        return n
    def U(s):
        if s.peek() in ('+', '-'):
            op = s.eat(); return ('U', ('tok', op[1]), s.U())
        return ('U', s.P())
    def P(s):
        f = s.F()
        if s.peek() == '^':
            s.eat(); return ('P', f, ('tok', '^'), s.U())
        return ('P', f)
    def F(s):
        n = ('F', s.A())
        while s.peek() == '!':
            s.eat(); n = ('F', n, ('tok', '!'))
        return n
    def A(s):
        k = s.peek()
        if k == 'NUM': return ('A', ('tok', s.eat()[1]))
        if k == '(':
            s.eat(); e = s.E(); s.eat(')'); return ('A', ('tok', '('), e, ('tok', ')'))
        if k == 'ID':
            name = s.eat()[1]
            if name in CONSTS: return ('A', ('tok', name))
            if name in F1:
                s.eat('('); e = s.E(); s.eat(')'); return ('A', ('tok', name), ('tok', '('), e, ('tok', ')'))
            if name in F2:
                s.eat('('); a = s.E(); s.eat(','); b = s.E(); s.eat(')')
                return ('A', ('tok', name), ('tok', '('), a, ('tok', ','), b, ('tok', ')'))
        raise Err('sintaxe')

def parse(s):
    p = Parser(tokenize(s)); t = p.E()
    if p.peek() != '$': raise Err('sintaxe')
    return t

# ---------- semântica (espelha runtime.c) ----------
class Dom(Exception): pass
def fin(r):
    if math.isnan(r) or math.isinf(r): raise Dom()
    return r
def rnd(x):
    f = abs(x); r = math.floor(f)
    if f - r >= 0.5: r += 1
    return math.copysign(r, x)

def make(deg):
    rad = (lambda x: x * math.pi / 180.0) if deg else (lambda x: x)
    back = (lambda x: x * 180.0 / math.pi) if deg else (lambda x: x)
    def sin(x):
        if deg:
            y = math.fmod(x, 360.0); y += 360.0 if y < 0 else 0
            if y in (0.0, 180.0): return 0.0
            if y == 90.0: return 1.0
            if y == 270.0: return -1.0
        return math.sin(rad(x))
    def cos(x):
        if deg:
            y = math.fmod(x, 360.0); y += 360.0 if y < 0 else 0
            if y in (90.0, 270.0): return 0.0
            if y == 0.0: return 1.0
            if y == 180.0: return -1.0
        return math.cos(rad(x))
    def tan(x):
        if deg:
            y = math.fmod(x, 180.0); y += 180.0 if y < 0 else 0
            if y == 90.0: raise Dom()
            if y == 0.0: return 0.0
        elif abs(math.cos(x)) < 1e-15: raise Dom()
        return fin(math.tan(rad(x)))
    def asin(x):
        if abs(x) > 1: raise Dom()
        return back(math.asin(x))
    def acos(x):
        if abs(x) > 1: raise Dom()
        return back(math.acos(x))
    def ov(f):
        def g(*a):
            try: return fin(f(*a))
            except OverflowError: raise Dom()
        return g
    def pos(f):
        def g(x):
            if x <= 0: raise Dom()
            return f(x)
        return g
    def sqrt(x):
        if x < 0: raise Dom()
        return math.sqrt(x)
    def powf(a, b):
        if a == 0.0 and b < 0.0: raise Dom()
        if a < 0.0 and b != math.floor(b): raise Dom()
        try: return fin(math.pow(a, b))
        except OverflowError: raise Dom()
    def root(x, n):
        if n == 0.0: raise Dom()
        if x < 0.0:
            if n == math.floor(n) and math.fmod(n, 2.0) != 0.0: return -math.pow(-x, 1.0 / n)
            raise Dom()
        try: return fin(math.pow(x, 1.0 / n))
        except OverflowError: raise Dom()
    f1 = dict(sin=sin, cos=cos, tan=tan, asin=asin, acos=acos, atan=lambda x: back(math.atan(x)),
              sinh=ov(math.sinh), cosh=ov(math.cosh), tanh=math.tanh, sqrt=sqrt, cbrt=math.cbrt,
              exp=ov(math.exp), ln=pos(math.log), log=pos(math.log10), log2=pos(math.log2),
              abs=abs, floor=lambda x: float(math.floor(x)), ceil=lambda x: float(math.ceil(x)), round=rnd)
    f2 = dict(max=lambda a, b: a if a > b else b, min=lambda a, b: a if a < b else b,
              atan2=lambda y, x: back(math.atan2(y, x)), hypot=ov(math.hypot), pow=powf, root=root)
    return f1, f2

def evaluate(tree, deg=False):
    f1, f2 = make(deg)
    def ev(n):
        k = n[0]
        if k == 'tok': return n[1]
        c = n[1:]
        if k == 'E':
            if len(c) == 1: return ev(c[0])
            a, op, b = ev(c[0]), c[1][1], ev(c[2])
            return fin(a + b if op == '+' else a - b)
        if k == 'T':
            if len(c) == 1: return ev(c[0])
            a, op, b = ev(c[0]), c[1][1], ev(c[2])
            if op == '*': return fin(a * b)
            if b == 0.0: raise Dom()
            return fin(a / b) if op == '/' else math.fmod(a, b)
        if k == 'U':
            if len(c) == 1: return ev(c[0])
            v = ev(c[1]); return -v if c[0][1] == '-' else v
        if k == 'P':
            if len(c) == 1: return ev(c[0])
            return f2['pow'](ev(c[0]), ev(c[2]))
        if k == 'F':
            if len(c) == 1: return ev(c[0])
            a = ev(c[0])
            if a < 0 or a != math.floor(a) or a > 170: raise Dom()
            r = 1.0
            for i in range(2, int(a) + 1): r *= i
            return r
        if k == 'A':
            t = c[0][1]
            if len(c) == 1: return CONSTS[t] if t in CONSTS else float(t)
            if t == '(': return ev(c[1])
            if t in f1: return f1[t](ev(c[2]))
            return f2[t](ev(c[2]), ev(c[4]))
    return ev(tree)

# ---------- derivação à esquerda ----------
def leftmost(tree):
    """Devolve a lista de (regra, forma sentencial) da derivação mais à esquerda."""
    def rule(n):
        k = n[0]; ch = n[1:]
        rhs = ' '.join(c[0] if c[0] != 'tok' else c[1] for c in ch)
        return k + ' → ' + rhs
    form = [tree]; steps = [('', 'E')]
    while True:
        idx = next((i for i, x in enumerate(form) if x[0] != 'tok'), None)
        if idx is None: break
        n = form[idx]
        form = form[:idx] + list(n[1:]) + form[idx + 1:]
        steps.append((rule(n), ' '.join(x[0] if x[0] != 'tok' else x[1] for x in form)))
    return steps

def to_dot(tree):
    lines = ['digraph G { rankdir=TB; node [shape=circle,fontname="Helvetica",fontsize=11,width=0.38,fixedsize=true]; edge [arrowsize=0.5];']
    cnt = [0]
    def go(n):
        cnt[0] += 1; me = cnt[0]
        if n[0] == 'tok':
            lines.append('n%d [label="%s",shape=box,style="rounded,filled",fillcolor="#e8eef7",fixedsize=false];' % (me, n[1]))
        else:
            lines.append('n%d [label="%s"];' % (me, n[0]))
            for c in n[1:]:
                ch = go(c); lines.append('n%d -> n%d;' % (me, ch))
        return me
    go(tree); lines.append('}')
    return '\n'.join(lines)

if __name__ == '__main__':
    t = parse('2+3*4')
    for r, f in leftmost(t): print('%-18s %s' % (r, f))
    print(evaluate(t))
