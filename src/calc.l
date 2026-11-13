%option noyywrap nounput noinput yylineno
%{
/* calc.l - analisador léxico (Flex)
 * A ER de NUMBER é a obtida por eliminação de estados a partir do DFA
 * (ver artigo, Seção 4): (d+(p d*)? + p d+)(x s? d+)?                   */
#include <stdlib.h>
#include <string.h>
#include "calc.h"
#include "calc.tab.h"

#define YY_USER_ACTION tok_line = yylineno - (yytext[0] == '\n' ? 1 : 0);
%}

DIGIT   [0-9]
EXPO    [eE][+-]?{DIGIT}+
NUMBER  ({DIGIT}+(\.{DIGIT}*)?|\.{DIGIT}+){EXPO}?
IDENT   [A-Za-z_][A-Za-z0-9_]*

%%
{NUMBER}    { yylval.num = strtod(yytext, NULL); return NUMBER; }
{IDENT}     { return classify(yytext); }
"+"         { return ADD; }
"-"         { return SUB; }
"*"         { return MUL; }
"/"         { return DIV; }
"%"         { return MOD; }
"^"         { return POW; }
"!"         { return FACT; }
"("         { return LP; }
")"         { return RP; }
","         { return COMMA; }
"="         { return ASSIGN; }
[\n;]       { return SEP; }
[ \t\r]+    { /* espaços são ignorados */ }
"#".*       { /* comentário até o fim da linha */ }
<<EOF>>     { static int sent = 0; if (!sent) { sent = 1; return SEP; } return 0; }
.           { return BAD; }
%%
