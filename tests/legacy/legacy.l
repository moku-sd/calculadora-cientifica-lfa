%option noyywrap
%{
/* Reprodução do analisador do trabalho de referência (Fig. 22): ER com sinal embutido e ponto obrigatório. */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "legacy.tab.h"
%}
%%
"+"   { return ADD; }
"-"   { return SUB; }
"*"   { return MUL; }
"/"   { return DIV; }
"("   { return OP; }
")"   { return CP; }
"sin" { return SIN; }
[+-]?(([0-9]+\.[0-9]+)|(\.[0-9]+)|([0-9]+\.))   { sscanf(yytext, "%lf", &yylval); return NUMBER; }
\n    { return EOL; }
[ \t] { }
.     { fprintf(stderr, "Mystery character %s\n", yytext); }
%%
