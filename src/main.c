/* main.c - ponto de entrada.
 *   calc              lê comandos da entrada padrão (REPL se for terminal)
 *   calc -e "expr"    avalia uma expressão e sai
 *   calc --tokens     modo de depuração léxica: imprime os tokens de cada linha */
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "calc.h"
#include "calc.tab.h"

int yyparse(void);
int yylex(void);
typedef struct yy_buffer_state *YY_BUFFER_STATE;
YY_BUFFER_STATE yy_scan_string(const char *);
extern char *yytext;

int main(int argc, char **argv)
{
    sym_define(sym_lookup("ans"), 0.0);
    if (argc > 1 && !strcmp(argv[1], "--tokens")) {
        int t, first = 1;
        while ((t = yylex()) != 0) {
            if (t == SEP) { printf("%sSEP\n", first ? "" : " "); first = 1; continue; }
            printf("%s%s(%s)", first ? "" : " ", token_name(t), yytext);
            first = 0;
        }
        return 0;
    }
    if (argc > 2 && !strcmp(argv[1], "-e")) {
        yy_scan_string(argv[2]);
    } else {
        interactive = isatty(0);
        if (interactive) { printf("calc: calculadora científica (LFA/UFSC). 'deg', 'rad', 'vars'. Ctrl-D sai.\n> "); fflush(stdout); }
    }
    yyparse();
    return n_errors ? 1 : 0;
}
