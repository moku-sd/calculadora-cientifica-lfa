import json, subprocess, sys
sys.path.insert(0, '.')
import gramatica as G
j = json.load(open('build/automato.json'))
FONT = 'DejaVu Sans'
def render(name, dot, dpi=220):
    open(f'fig/{name}.dot', 'w').write(dot)
    subprocess.run(['dot', '-Tpng', f'-Gdpi={dpi}', f'fig/{name}.dot', '-o', f'fig/{name}.png'], check=True)

def automaton(states, start, final, edges, labels=None, rankdir='LR'):
    L = [f'digraph A {{ rankdir={rankdir}; nodesep=0.45; ranksep=0.7; node [shape=circle,fontname="{FONT}",fontsize=13]; edge [fontname="{FONT}",fontsize=13,arrowsize=0.8];',
         'start [shape=point,width=0.01,label=""];']
    for s in states:
        lab = (labels or {}).get(s, s)
        shp = 'doublecircle' if s in final else 'circle'
        L.append(f'"{s}" [label="{lab}",shape={shp}];')
    L.append(f'start -> "{start}";')
    merged = {}
    for (a, b), sym in edges: merged.setdefault((a, b), []).append(sym)
    for (a, b), syms in merged.items():
        L.append(f'"{a}" -> "{b}" [label="{", ".join(syms)}"];')
    L.append('}')
    return '\n'.join(L)

# ε-NFA
nfa = j['nfa']; edges = []
for k, v in nfa['delta'].items():
    q, a = k.split('|')
    for r in v: edges.append(((q, r), a))
render('enfa', automaton(nfa['states'], nfa['start'], set(nfa['final']), edges))
# DFA
dfa = j['dfa']; edges = [((k.split('|')[0], v), k.split('|')[1]) for k, v in dfa['delta'].items()]
labels = {n: n + '\\n{' + ','.join(s) + '}' for n, s in dfa['states']}
render('dfa', automaton([n for n, _ in dfa['states']], dfa['start'], set(dfa['final']), edges, labels))
# pipeline
render('pipeline', f'''digraph P {{ rankdir=LR; nodesep=0.35; ranksep=0.45; node [shape=box,style="rounded,filled",fillcolor="#eef2f8",fontname="{FONT}",fontsize=12]; edge [arrowsize=0.7,fontname="{FONT}",fontsize=10];
enfa [label="ε-NFA"]; dfa [label="DFA"]; er [label="ER"]; cfg [label="CFG\\n(E,T,U,P,F,A)"]; flex [label="Flex",fillcolor="#fff3d6"]; bison [label="Bison",fillcolor="#fff3d6"]; scan [label="scanner\\n(lex.yy.c)"]; parser [label="parser\\n(calc.tab.c)"]; gcc [label="gcc",fillcolor="#e1f0e1"]; calc [label="calc",fillcolor="#e1f0e1"];
enfa -> dfa [label="subconjuntos"]; dfa -> er [label="eliminação\\nde estados"]; er -> flex; cfg -> bison; flex -> scan; bison -> parser; scan -> gcc; parser -> gcc; gcc -> calc; }}''')
# árvore de análise
render('arvore', G.to_dot(G.parse('2+3*4')).replace('rankdir=TB;', 'rankdir=TB; nodesep=0.12; ranksep=0.28;'), 200)
print('ok')
