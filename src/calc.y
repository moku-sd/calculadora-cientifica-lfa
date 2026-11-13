%code requires { #include "calc.h" }
%{
/* calc.y - gramática livre de contexto (Bison)
 * Estratificada (E, T, U, P, F, A): não usa declarações de precedência,
 * a hierarquia de não terminais codifica precedência e associatividade.  */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
extern char *yytext;
int  yylex(void);
void yyerror(const char *msg);
%}

%union {
    double  num;
    double (*f1)(double);
    double (*f2)(double, double);
    Symbol *sym;
}

%token <num> NUMBER CONST
%token <f1>  FUNC1
%token <f2>  FUNC2
%token <sym> ID
%token ADD SUB MUL DIV MOD POW FACT LP RP COMMA ASSIGN SEP BAD
%token CMD_DEG CMD_RAD CMD_VARS

%type <num> expr term unary power post atom
%start program

%%
program : %empty
        | program stmt
        ;

stmt    : SEP                    { /* linha vazia */ }
        | expr SEP               { show_result($1); end_stmt(); }
        | ID ASSIGN expr SEP     { if (!sem_err) { sym_define($1, $3); show_result($3); } end_stmt(); }
        | CMD_DEG SEP            { set_mode(1); end_stmt(); }
        | CMD_RAD SEP            { set_mode(0); end_stmt(); }
        | CMD_VARS SEP           { sym_list(); end_stmt(); }
        | error SEP              { yyerrok; end_stmt(); }
        ;

expr    : term                   { $$ = $1; }
        | expr ADD term          { $$ = op_add($1, $3); }
        | expr SUB term          { $$ = op_sub($1, $3); }
        ;

term    : unary                  { $$ = $1; }
        | term MUL unary         { $$ = op_mul($1, $3); }
        | term DIV unary         { $$ = op_div($1, $3); }
        | term MOD unary         { $$ = op_mod($1, $3); }
        ;

unary   : power                  { $$ = $1; }
        | ADD unary              { $$ = $2; }
        | SUB unary              { $$ = -$2; }
        ;

power   : post                   { $$ = $1; }
        | post POW unary         { $$ = op_pow($1, $3); }
        ;

post    : atom                   { $$ = $1; }
        | post FACT              { $$ = op_fact($1); }
        ;

atom    : NUMBER                 { $$ = $1; }
        | CONST                  { $$ = $1; }
        | ID                     { $$ = use_var($1); }
        | LP expr RP             { $$ = $2; }
        | FUNC1 LP expr RP       { $$ = $1($3); }
        | FUNC2 LP expr COMMA expr RP { $$ = $1($3, $5); }
        ;
%%

void yyerror(const char *msg)
{
    (void)msg;
    if (!sem_err) {
        if (yytext[0] == '\n' || yytext[0] == '\0' || yytext[0] == ';')
            fprintf(stderr, "linha %d: erro de sintaxe: expressão incompleta\n", tok_line);
        else
            fprintf(stderr, "linha %d: erro de sintaxe perto de '%s'\n", tok_line, yytext);
    }
    sem_err = 1;
}
