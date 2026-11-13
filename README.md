# Calculadora científica estendida (LFA – UFSC)

Do ε-NFA ao executável: autômato → DFA → ER (Flex) e CFG (Bison).

## Requisitos
`flex`, `bison`, `gcc`, `python3` (e `graphviz` só para regerar as figuras).

## Reproduzir
```
mkdir -p build fig
make                       # bison + flex + gcc  -> ./calc
python3 automato.py        # ε-NFA -> DFA -> DFA mínimo -> ER, com verificação exaustiva (1,4 mi strings)
python3 tests/run_tests.py # casos fixos, varredura léxica, teste diferencial C x Python
```

## Usar
```
./calc                 # lê comandos da entrada padrão (REPL em terminal)
./calc -e "sin(pi/6)"  # avalia uma expressão
./calc --tokens        # depuração léxica
```
Comandos: `deg`, `rad`, `vars`, `x = expr`, `ans`; comentários com `#`.

## Arquivos
- `src/calc.l`   analisador léxico (ER derivada do DFA)
- `src/calc.y`   gramática estratificada (29 produções, 0 conflitos)
- `src/runtime.c` tabela de símbolos, funções, verificação de domínio
- `automato.py`  construção e verificação das etapas formais
- `gramatica.py` implementação independente da CFG (derivação, árvore, oráculo do teste diferencial)
- `tests/`       suíte de testes (+ `legacy/`, reconstrução do trabalho de referência)
