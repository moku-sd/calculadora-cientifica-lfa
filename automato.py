#!/usr/bin/env python3
"""ε-NFA -> DFA (construção de subconjuntos) -> DFA mínimo -> ER (eliminação de estados).
Alfabeto por classes: d = dígito, p = ponto, x = e|E, s = sinal (+|-).
Tudo é verificado por enumeração exaustiva contra uma ER de referência."""
import itertools, json, re, sys
from collections import OrderedDict

SIGMA = ['d', 'p', 'x', 's']
EPS = 'ε'

# ---------- ε-NFA ----------
NFA_STATES = ['q0','q1','q2','q3','q4','q5','q6','q7']
NFA_START = 'q0'
NFA_FINAL = {'q4', 'q7'}
NFA = {  # (estado, símbolo) -> conjunto
    ('q0','d'):{'q1'}, ('q0','p'):{'q3'},
    ('q1','d'):{'q1'}, ('q1','p'):{'q2'}, ('q1',EPS):{'q4'},
    ('q2','d'):{'q2'}, ('q2',EPS):{'q4'},
    ('q3','d'):{'q2'},
    ('q4','x'):{'q5'},
    ('q5','s'):{'q6'}, ('q5',EPS):{'q6'},
    ('q6','d'):{'q7'},
    ('q7','d'):{'q7'},
}
def nd(q, a): return NFA.get((q, a), set())

def eclose(S):
    S = set(S); stack = list(S)
    while stack:
        q = stack.pop()
        for r in nd(q, EPS):
            if r not in S: S.add(r); stack.append(r)
    return frozenset(S)

def move(S, a):
    out = set()
    for q in S: out |= nd(q, a)
    return out

def name(S): return '{' + ','.join(sorted(S, key=lambda z:int(z[1:]))) + '}' if S else '∅'

# ---------- subconjuntos ----------
def subset_construction():
    start = eclose({NFA_START})
    states = OrderedDict([(start, None)])
    trans = {}
    work = [start]
    log = []
    while work:
        S = work.pop(0)
        for a in SIGMA:
            m = move(S, a)
            T = eclose(m) if m else frozenset()
            log.append((S, a, frozenset(m), T))
            trans[(S, a)] = T
            if T and T not in states:
                states[T] = None; work.append(T)
    return start, list(states), trans, log

# ---------- DFA com nomes A,B,C... ----------
def label_dfa(start, states, trans):
    names = {S: 'A%d' % i for i, S in enumerate(states)}   # A0 = inicial
    final = {names[S] for S in states if S & NFA_FINAL}
    t = {}
    for S in states:
        for a in SIGMA:
            T = trans[(S, a)]
            if T: t[(names[S], a)] = names[T]
    return names, 'A0', final, t

def minimize(states, start, final, t):
    # refinamento de partições (Moore)
    part = {s: (s in final) for s in states}
    while True:
        sig = {s: (part[s], tuple(part.get(t.get((s, a))) if t.get((s, a)) else None for a in SIGMA)) for s in states}
        ids = {}; new = {}
        for s in states:
            new[s] = ids.setdefault(sig[s], len(ids))
        if len(set(new.values())) == len(set(part.values())):
            part = new; break
        part = new
    classes = {}
    for s in states: classes.setdefault(part[s], []).append(s)
    order = sorted(classes, key=lambda c: min(int(x[1:]) for x in classes[c]))
    rename = {}
    for i, c in enumerate(order):
        for s in classes[c]: rename[s] = 'M%d' % i
    mt = {}
    for (s, a), r in t.items(): mt[(rename[s], a)] = rename[r]
    mstates = sorted(set(rename.values()), key=lambda z:int(z[1:]))
    mfinal = {rename[s] for s in final}
    return mstates, rename[start], mfinal, mt, classes, rename

# ---------- simulação ----------
def run_nfa(w):
    S = eclose({NFA_START})
    for c in w:
        S = eclose(move(S, c))
        if not S: return False
    return bool(S & NFA_FINAL)

def run_dfa(start, final, t, w):
    q = start
    for c in w:
        q = t.get((q, c))
        if q is None: return False
    return q in final

# ---------- ER por eliminação de estados ----------
# ER como árvores: ('0',) vazio, ('e',) epsilon, ('s','d'), ('u',a,b), ('c',a,b), ('*',a)
Z = ('0',); E = ('e',)
def U(a, b):
    if a == Z: return b
    if b == Z: return a
    if a == b: return a
    return ('u', a, b)
def C(a, b):
    if a == Z or b == Z: return Z
    if a == E: return b
    if b == E: return a
    return ('c', a, b)
def K(a):
    if a == Z or a == E: return E
    if a[0] == '*': return a
    return ('*', a)
def show(r, top=True):
    k = r[0]
    if k == '0': return '∅'
    if k == 'e': return 'ε'
    if k == 's': return r[1]
    if k == '*':
        a = r[1]
        return (show(a, False) if a[0] == 's' else '(' + show(a) + ')') + '*'
    if k == 'u':
        s = show(r[1]) + ' + ' + show(r[2])
        return s if top else '(' + s + ')'
    if k == 'c':
        def f(x):
            return '(' + show(x) + ')' if x[0] == 'u' else show(x, False)
        return f(r[1]) + f(r[2])
def to_py(r):
    k = r[0]
    if k == '0': return '(?!)'
    if k == 'e': return '(?:)'
    if k == 's': return {'d':'D','p':'P','x':'X','s':'S'}[r[1]]
    if k == '*': return '(?:' + to_py(r[1]) + ')*'
    if k == 'u': return '(?:' + to_py(r[1]) + '|' + to_py(r[2]) + ')'
    if k == 'c': return to_py(r[1]) + to_py(r[2])

def dfa_to_re(states, start, final, t, order=None):
    # GNFA com estados novos S (início) e F (final)
    R = {}
    def get(i, j): return R.get((i, j), Z)
    for (q, a), r in t.items(): R[(q, r)] = U(get(q, r), ('s', a))
    for f in final: R[(f, 'F')] = U(get(f, 'F'), E)
    R[('S', start)] = E
    steps = []
    remaining = list(order if order else [s for s in states])
    for q in remaining:
        loop = K(get(q, q))
        ins = [i for i in ['S'] + remaining if i != q and get(i, q) != Z]
        outs = [j for j in remaining + ['F'] if j != q and get(q, j) != Z]
        changed = []
        for i in ins:
            for j in outs:
                R[(i, j)] = U(get(i, j), C(C(get(i, q), loop), get(q, j)))
                changed.append((i, j, show(R[(i, j)])))
        for k in list(R):
            if q in k: del R[k]
        remaining_after = [x for x in remaining if x != q]
        steps.append((q, changed))
        # (remaining é recalculado no laço seguinte pela filtragem acima)
        remaining = remaining  # mantém a lista; estados removidos não têm mais arestas
    return get('S', 'F'), steps

# ---------- referência (fechada) ----------
REF = r'(?:D+(?:PD*)?|PD+)(?:XS?D+)?'
def ref_match(w):
    s = ''.join({'d':'D','p':'P','x':'X','s':'S'}[c] for c in w)
    return re.fullmatch(REF.replace('(?:XS?D+)?','(?:XS?D+)?'), s) is not None

def main():
    start, sets, trans, log = subset_construction()
    names, dstart, dfinal, dt = label_dfa(start, sets, trans)
    dstates = [names[S] for S in sets]
    mstates, mstart, mfinal, mt, classes, rename = minimize(dstates, dstart, dfinal, dt)
    # ER por eliminação, no DFA mínimo (ordem: do último para o primeiro, exceto o inicial)
    order = [s for s in mstates if s != mstart][::-1] + [mstart]
    ER, steps = dfa_to_re(mstates, mstart, mfinal, mt, order)
    ER_py = re.compile(to_py(ER))
    # ---- verificação exaustiva até |w| <= 10 ----
    bad = 0; total = 0; acc = 0
    for n in range(0, 11):
        for tup in itertools.product(SIGMA, repeat=n):
            w = ''.join(tup); total += 1
            a = run_nfa(w); b = run_dfa(dstart, dfinal, dt, w); c = run_dfa(mstart, mfinal, mt, w)
            s = ''.join({'d':'D','p':'P','x':'X','s':'S'}[ch] for ch in w)
            d = ER_py.fullmatch(s) is not None
            e = re.fullmatch(REF, s) is not None
            acc += a
            if not (a == b == c == d == e):
                bad += 1
                if bad < 5: print('DISCORDÂNCIA', w, a, b, c, d, e)
    print(f'strings verificadas: {total}  aceitas: {acc}  discordâncias: {bad}')
    out = dict(
        nfa=dict(states=NFA_STATES, start=NFA_START, final=sorted(NFA_FINAL),
                 delta={f'{q}|{a}': sorted(v) for (q, a), v in NFA.items()}),
        closure={q: sorted(eclose({q}), key=lambda z:int(z[1:])) for q in NFA_STATES},
        dfa=dict(states=[(names[S], sorted(S, key=lambda z:int(z[1:]))) for S in sets],
                 start=dstart, final=sorted(dfinal), delta={f'{q}|{a}': r for (q, a), r in dt.items()}),
        log=[(name(S), a, name(M), name(T)) for S, a, M, T in log],
        min=dict(states=mstates, start=mstart, final=sorted(mfinal), delta={f'{q}|{a}': r for (q, a), r in mt.items()},
                 classes={ 'M%d' % i: sorted(v, key=lambda z:int(z[1:])) for i, (k, v) in enumerate(sorted(classes.items(), key=lambda kv: min(int(x[1:]) for x in kv[1]))) }),
        er_elim=show(ER), er_ref='(d+(p d*)? + p d+)(x s? d+)?', total=total, accepted=acc, bad=bad,
        steps=[(q, ch) for q, ch in steps])
    json.dump(out, open('build/automato.json', 'w'), ensure_ascii=False, indent=1)
    print('DFA:', len(dstates), 'estados | mínimo:', len(mstates), 'estados')
    print('ER (eliminação):', show(ER))
    return bad

if __name__ == '__main__':
    sys.exit(1 if main() else 0)
