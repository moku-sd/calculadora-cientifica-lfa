%{
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#define YYSTYPE double
int yylex(void); int yyerror(const char *s) { fprintf(stderr, "error: %s\n", s); return 0; }
%}
%token NUMBER ADD SUB MUL DIV OP CP EOL SIN
%%
calclist: | calclist exp EOL { printf("= %f\n", $2); } | calclist EOL ;
exp: factor | exp ADD factor { $$ = $1 + $3; } | exp SUB factor { $$ = $1 - $3; } ;
factor: term | factor MUL term { $$ = $1 * $3; } | factor DIV term { $$ = $1 / $3; } ;
term: NUMBER | ADD term { $$ = $2; } | SUB term { $$ = -$2; } | OP exp CP { $$ = $2; } | SIN term { $$ = sin($2); } ;
%%
int main(void) { return yyparse(); }
