/* calc.h - declarações compartilhadas entre o analisador léxico, o sintático e o runtime */
#ifndef CALC_H
#define CALC_H

typedef struct Symbol {
    char *name;
    double value;
    int defined;
    struct Symbol *next;
} Symbol;

extern int  tok_line;      /* linha do último token lido (para mensagens de erro) */
extern int  angle_deg;     /* 1 = graus, 0 = radianos */
extern int  sem_err;       /* erro semântico pendente no comando atual */
extern int  n_errors;      /* total de erros (código de saída) */
extern int  interactive;

/* tabela de símbolos */
Symbol *sym_lookup(const char *name);
void    sym_define(Symbol *s, double v);
void    sym_list(void);
int     classify(const char *text);          /* identificador -> token */
const char *token_name(int tok);

/* semântica */
double fail(const char *fmt, ...);
double op_add(double a, double b);
double op_sub(double a, double b);
double op_mul(double a, double b);
double op_div(double a, double b);
double op_mod(double a, double b);
double op_pow(double a, double b);
double op_fact(double a);
double use_var(Symbol *s);
void   show_result(double v);
void   end_stmt(void);
void   set_mode(int deg);

#endif
