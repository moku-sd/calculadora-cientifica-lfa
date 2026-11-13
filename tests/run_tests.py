#!/usr/bin/env python3
import itertools, json, math, random, subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '.')
import gramatica as G
import automato as A

CALC = './calc'
def run(src):
    p = subprocess.run([CALC], input=src, capture_output=True, text=True)
    return p.stdout, p.stderr, p.returncode

def value(out):
    ls = [l for l in out.splitlines() if l.startswith('= ')]
    return float(ls[-1][2:]) if ls else None

def close(a, b): return abs(a - b) <= 1e-12 * max(1.0, abs(b))

results = {}
fails = 0

# ---------------- 1. casos fixos (oráculo: biblioteca math do Python) ----------------
rad = lambda x: x * math.pi / 180
FIXED = [  # (grupo, entrada, esperado | None para erro, modo)
 ('Literais', '42', 42, ''), ('Literais', '3.14', 3.14, ''), ('Literais', '.5', 0.5, ''), ('Literais', '7.', 7, ''),
 ('Literais', '1e3', 1000, ''), ('Literais', '2.5E-3', 0.0025, ''), ('Literais', '.5e+2', 50, ''),
 ('Aritmética', '7.8 + 4.3', 12.1, ''), ('Aritmética', '7.6-3.2', 4.4, ''), ('Aritmética', '9.2 * 4.8', 44.16, ''),
 ('Aritmética', '9.2 / 3.8', 9.2 / 3.8, ''), ('Aritmética', '5.1 + (2.1 - 1.1)', 6.1, ''),
 ('Aritmética', '10 % 3', 1, ''), ('Aritmética', '-7 % 3', -1, ''),
 ('Precedência', '2 + 3 * 4', 14, ''), ('Precedência', '(2 + 3) * 4', 20, ''), ('Precedência', '2 ^ 3 ^ 2', 512, ''),
 ('Precedência', '-2 ^ 2', -4, ''), ('Precedência', '2 ^ -3', 0.125, ''), ('Precedência', '10 - 4 - 3', 3, ''),
 ('Precedência', '2 * -3', -6, ''), ('Precedência', '--4', 4, ''), ('Precedência', '2 ^ 3 !', 64, ''), ('Precedência', '-3 !', -6, ''),
 ('Fatorial', '0!', 1, ''), ('Fatorial', '5!', 120, ''), ('Fatorial', '10!', 3628800, ''), ('Fatorial', '170!', math.factorial(170), ''),
 ('Trigonometria (rad)', 'sin(0.5)', math.sin(0.5), ''), ('Trigonometria (rad)', 'cos(pi)', -1, ''),
 ('Trigonometria (rad)', 'sin(pi/6)', math.sin(math.pi / 6), ''), ('Trigonometria (rad)', 'atan(1)*4', math.pi, ''),
 ('Trigonometria (rad)', 'asin(1)', math.pi / 2, ''), ('Trigonometria (rad)', 'tan(pi/4)', math.tan(math.pi / 4), ''),
 ('Trigonometria (graus)', 'sin(90)', 1, 'deg\n'), ('Trigonometria (graus)', 'cos(60)', math.cos(rad(60)), 'deg\n'),
 ('Trigonometria (graus)', 'tan(45)', math.tan(rad(45)), 'deg\n'), ('Trigonometria (graus)', 'sin(180)', 0, 'deg\n'),
 ('Trigonometria (graus)', 'acos(0.5)', 60, 'deg\n'), ('Trigonometria (graus)', 'atan2(1, 1)', 45, 'deg\n'),
 ('Hiperbólicas, exp, log', 'sinh(1)', math.sinh(1), ''), ('Hiperbólicas, exp, log', 'tanh(0.5)', math.tanh(0.5), ''),
 ('Hiperbólicas, exp, log', 'exp(1)', math.e, ''), ('Hiperbólicas, exp, log', 'ln(e)', 1, ''),
 ('Hiperbólicas, exp, log', 'log(1000)', 3, ''), ('Hiperbólicas, exp, log', 'log2(1024)', 10, ''),
 ('Raízes e arredondamento', 'sqrt(2)', math.sqrt(2), ''), ('Raízes e arredondamento', 'cbrt(-27)', -3, ''),
 ('Raízes e arredondamento', 'root(-32, 5)', -2, ''), ('Raízes e arredondamento', 'root(81, 4)', 3, ''),
 ('Raízes e arredondamento', 'floor(-2.5)', -3, ''), ('Raízes e arredondamento', 'ceil(2.1)', 3, ''),
 ('Raízes e arredondamento', 'round(2.5)', 3, ''), ('Raízes e arredondamento', 'round(-2.5)', -3, ''), ('Raízes e arredondamento', 'abs(-8.25)', 8.25, ''),
 ('Funções de dois argumentos', 'max(3, 7)', 7, ''), ('Funções de dois argumentos', 'min(3, -7)', -7, ''),
 ('Funções de dois argumentos', 'hypot(3, 4)', 5, ''), ('Funções de dois argumentos', 'pow(2, 10)', 1024, ''),
 ('Constantes', 'pi', math.pi, ''), ('Constantes', 'tau', 2 * math.pi, ''), ('Constantes', 'phi', (1 + 5 ** .5) / 2, ''),
 ('Variáveis', 'x = 10\ny = x * 2\ny + ans', 40, ''), ('Variáveis', '3 + 4\nans * 2', 14, ''),
 ('Variáveis', 'r = 2; pi * r ^ 2', math.pi * 4, ''), ('Variáveis', 'a = 1 # comentário\na + 1', 2, ''),
 ('Erros semânticos', '4 / 0', None, ''), ('Erros semânticos', '-4.0 / 0.0', None, ''), ('Erros semânticos', '5 % 0', None, ''),
 ('Erros semânticos', 'sqrt(-1)', None, ''), ('Erros semânticos', 'ln(0)', None, ''), ('Erros semânticos', 'log(-5)', None, ''),
 ('Erros semânticos', 'asin(2)', None, ''), ('Erros semânticos', 'tan(90)', None, 'deg\n'), ('Erros semânticos', '(-8) ^ 0.5', None, ''),
 ('Erros semânticos', '0 ^ -1', None, ''), ('Erros semânticos', '2.5!', None, ''), ('Erros semânticos', '171!', None, ''),
 ('Erros semânticos', '1e200 * 1e200', None, ''), ('Erros semânticos', 'exp(1000)', None, ''), ('Erros semânticos', 'z + 1', None, ''),
 ('Erros sintáticos', '3 +', None, ''), ('Erros sintáticos', '(1 + 2', None, ''), ('Erros sintáticos', '2 3', None, ''),
 ('Erros sintáticos', '4 $ 5', None, ''), ('Erros sintáticos', 'sin 3', None, ''), ('Erros sintáticos', 'max(1)', None, ''),
 ('Erros sintáticos', 'pi = 3', None, ''), ('Erros sintáticos', '1e', None, ''),
]
rows = []
for grp, expr, exp, pre in FIXED:
    out, err, rc = run(pre + expr + '\n')
    v = value(out)
    ok = (v is None and exp is None and rc == 1) if exp is None else (v is not None and close(v, exp))
    if not ok:
        fails += 1; print('FALHOU', repr(expr), 'esperado', exp, 'obtido', v, err.strip())
    rows.append(dict(grupo=grp, entrada=expr.replace('\n', ' ⏎ '), modo='graus' if pre else 'rad',
                     esperado=('erro' if exp is None else repr(exp)), obtido=(out.strip().splitlines()[-1] if v is not None else err.strip().splitlines()[0] if err else '—'), ok=ok))
results['fixos'] = dict(total=len(FIXED), ok=sum(r['ok'] for r in rows), rows=rows)
print(f"[1] casos fixos: {results['fixos']['ok']}/{len(FIXED)}")

# ---------------- 2. varredura léxica exaustiva contra o DFA ----------------
alpha = ['0', '1', '.', 'e', 'E', '+', '-']
cls = {'0': 'd', '1': 'd', '.': 'p', 'e': 'x', 'E': 'x', '+': 's', '-': 's'}
start, sets, trans, _ = A.subset_construction()
names, dstart, dfinal, dt = A.label_dfa(start, sets, trans)
words = []
MAXLEN = 7
for n in range(1, MAXLEN + 1):
    words += [''.join(t) for t in itertools.product(alpha, repeat=n)]
p = subprocess.run([CALC, '--tokens'], input='\n'.join(words) + '\n', capture_output=True, text=True)
lines = p.stdout.split('\n')
bad = 0; acc = 0
for w, l in zip(words, lines):
    toks = l.split(' ')
    one_num = len(toks) == 2 and toks[0] == 'NUMBER(%s)' % w and toks[1] == 'SEP'
    dfa = A.run_dfa(dstart, dfinal, dt, ''.join(cls[c] for c in w))
    acc += dfa
    if one_num != dfa:
        bad += 1
        if bad < 6: print('DISCORDÂNCIA léxica', repr(w), l, dfa)
fails += bad
results['lexico'] = dict(strings=len(words), aceitas=acc, discordancias=bad, maxlen=MAXLEN)
print(f'[2] varredura léxica: {len(words)} strings (|w|<={MAXLEN}), {acc} aceitas, {bad} discordâncias')

# ---------------- 3. teste diferencial C x Python (mesma CFG) ----------------
random.seed(2026)
def num():
    r = random.random()
    if r < .4: return str(random.randint(0, 12))
    if r < .7: return '%d.%d' % (random.randint(0, 9), random.randint(0, 99))
    if r < .8: return '.%d' % random.randint(1, 9)
    if r < .9: return '%de%s%d' % (random.randint(1, 9), random.choice(['', '+', '-']), random.randint(0, 4))
    return '%d.' % random.randint(1, 9)
def gen(d):
    if d <= 0 or random.random() < .2:
        return random.choice([num(), num(), num(), 'pi', 'e', 'phi'])
    r = random.random()
    if r < .45: return '%s %s %s' % (gen(d - 1), random.choice(['+', '-', '*', '/', '%', '^']), gen(d - 1))
    if r < .55: return '(%s)' % gen(d - 1)
    if r < .62: return '%s%s' % (random.choice(['-', '+']), gen(d - 1))
    if r < .67: return '(%s)!' % gen(d - 1)
    if r < .87: return '%s(%s)' % (random.choice(G.F1), gen(d - 1))
    return '%s(%s, %s)' % (random.choice(G.F2), gen(d - 1), gen(d - 1))
N = 6000
cases = [(gen(random.randint(1, 4)), random.random() < .35) for _ in range(N)]
def one(c):
    expr, deg = c
    out, err, rc = run(('deg\n' if deg else '') + expr + '\n')
    try:
        ref = G.evaluate(G.parse(expr), deg); refok = True
    except (G.Dom, OverflowError, ZeroDivisionError, ValueError):
        refok = False
    v = value(out)
    if refok:
        good = v is not None and close(v, ref)
    else:
        good = v is None and rc == 1
    return good, expr, deg, ref if refok else 'erro', v
with ThreadPoolExecutor(8) as ex: res = list(ex.map(one, cases))
bad = [r for r in res if not r[0]]
nerr = sum(1 for r in res if r[3] == 'erro')
for r in bad[:8]: print('DIVERGÊNCIA', r)
fails += len(bad)
results['diferencial'] = dict(total=N, divergencias=len(bad), com_erro=nerr, com_valor=N - nerr)
print(f'[3] teste diferencial: {N} expressões ({N-nerr} com valor, {nerr} com erro), {len(bad)} divergências')

# ---------------- 4. recuperação de erros: o REPL continua depois de um erro ----------------
out, err, rc = run('1 +\n2 * 3\n4 / 0\n5 + 5\n(\n7\n')
vals = [l for l in out.splitlines() if l.startswith('= ')]
ok = vals == ['= 6', '= 10', '= 7'] and rc == 1 and len(err.strip().splitlines()) == 3
results['recuperacao'] = dict(ok=ok, stdout=out, stderr=err)
fails += (not ok)
print('[4] recuperação de erros:', 'OK' if ok else 'FALHOU', out.split(), err.strip().splitlines())

json.dump(results, open('build/testes.json', 'w'), ensure_ascii=False, indent=1)
print('FALHAS TOTAIS:', fails)
sys.exit(1 if fails else 0)
