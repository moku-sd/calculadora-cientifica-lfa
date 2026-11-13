/* runtime.c - tabela de símbolos, funções matemáticas e semântica */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <unistd.h>
#include "calc.h"
#include "calc.tab.h"

int tok_line = 1, angle_deg = 0, sem_err = 0, n_errors = 0, interactive = 0;

#define PI 3.14159265358979323846

/* ---------- erros semânticos ---------- */
double fail(const char *fmt, ...)
{
    if (!sem_err) {
        va_list ap;
        fprintf(stderr, "linha %d: erro: ", tok_line);
        va_start(ap, fmt); vfprintf(stderr, fmt, ap); va_end(ap);
        fputc('\n', stderr);
    }
    sem_err = 1;
    return 0.0;
}
static double fin(double r)
{
    if (isnan(r)) return fail("resultado indefinido");
    if (isinf(r)) return fail("estouro de capacidade (resultado infinito)");
    return r;
}

/* ---------- operadores ---------- */
double op_add(double a, double b) { return fin(a + b); }
double op_sub(double a, double b) { return fin(a - b); }
double op_mul(double a, double b) { return fin(a * b); }
double op_div(double a, double b) { return b == 0.0 ? fail("divisão por zero") : fin(a / b); }
double op_mod(double a, double b) { return b == 0.0 ? fail("resto por zero") : fmod(a, b); }
double op_pow(double a, double b)
{
    if (a == 0.0 && b < 0.0) return fail("zero elevado a expoente negativo");
    if (a < 0.0 && b != floor(b)) return fail("base negativa com expoente não inteiro");
    return fin(pow(a, b));
}
double op_fact(double a)
{
    if (a < 0.0 || a != floor(a)) return fail("fatorial exige inteiro não negativo");
    if (a > 170.0) return fail("fatorial excede a capacidade do double (máx. 170!)");
    double r = 1.0;
    for (int i = 2; i <= (int)a; i++) r *= i;
    return r;
}

/* ---------- funções (modo graus/radianos) ---------- */
static double to_rad(double x) { return angle_deg ? x * PI / 180.0 : x; }
static double from_rad(double x) { return angle_deg ? x * 180.0 / PI : x; }

static double f_sin(double x)
{
    if (angle_deg) {                       /* valores exatos nos múltiplos de 90° */
        double y = fmod(x, 360.0); if (y < 0) y += 360.0;
        if (y == 0.0 || y == 180.0) return 0.0;
        if (y == 90.0) return 1.0;
        if (y == 270.0) return -1.0;
    }
    return sin(to_rad(x));
}
static double f_cos(double x)
{
    if (angle_deg) {
        double y = fmod(x, 360.0); if (y < 0) y += 360.0;
        if (y == 90.0 || y == 270.0) return 0.0;
        if (y == 0.0) return 1.0;
        if (y == 180.0) return -1.0;
    }
    return cos(to_rad(x));
}
static double f_tan(double x)
{
    if (angle_deg) {
        double y = fmod(x, 180.0); if (y < 0) y += 180.0;
        if (y == 90.0) return fail("tangente indefinida (múltiplo ímpar de 90 graus)");
        if (y == 0.0) return 0.0;
    } else if (fabs(cos(x)) < 1e-15) {
        return fail("tangente indefinida (múltiplo ímpar de pi/2)");
    }
    return fin(tan(to_rad(x)));
}
static double f_asin(double x) { return fabs(x) > 1.0 ? fail("asin definido apenas em [-1, 1]") : from_rad(asin(x)); }
static double f_acos(double x) { return fabs(x) > 1.0 ? fail("acos definido apenas em [-1, 1]") : from_rad(acos(x)); }
static double f_atan(double x) { return from_rad(atan(x)); }
static double f_sinh(double x) { return fin(sinh(x)); }
static double f_cosh(double x) { return fin(cosh(x)); }
static double f_tanh(double x) { return tanh(x); }
static double f_sqrt(double x) { return x < 0.0 ? fail("raiz quadrada de número negativo") : sqrt(x); }
static double f_cbrt(double x) { return cbrt(x); }
static double f_exp(double x)  { return fin(exp(x)); }
static double f_ln(double x)   { return x <= 0.0 ? fail("logaritmo de número não positivo") : log(x); }
static double f_log(double x)  { return x <= 0.0 ? fail("logaritmo de número não positivo") : log10(x); }
static double f_log2(double x) { return x <= 0.0 ? fail("logaritmo de número não positivo") : log2(x); }
static double f_abs(double x)  { return fabs(x); }
static double f_floor(double x){ return floor(x); }
static double f_ceil(double x) { return ceil(x); }
static double f_round(double x){ return round(x); }

static double g_max(double a, double b)   { return a > b ? a : b; }
static double g_min(double a, double b)   { return a < b ? a : b; }
static double g_atan2(double y, double x) { return from_rad(atan2(y, x)); }
static double g_hypot(double a, double b) { return fin(hypot(a, b)); }
static double g_pow(double a, double b)   { return op_pow(a, b); }
static double g_root(double x, double n)
{
    if (n == 0.0) return fail("raiz de índice zero");
    if (x < 0.0) {
        if (n == floor(n) && fmod(n, 2.0) != 0.0) return -pow(-x, 1.0 / n);
        return fail("raiz de índice par de número negativo");
    }
    return fin(pow(x, 1.0 / n));
}

/* ---------- tabelas de identificadores reservados ---------- */
static const struct { const char *n; double v; } consts[] = {
    {"pi", PI}, {"e", 2.71828182845904523536}, {"tau", 2.0 * PI}, {"phi", 1.61803398874989484820},
};
static const struct { const char *n; double (*f)(double); } funcs1[] = {
    {"sin", f_sin}, {"cos", f_cos}, {"tan", f_tan}, {"asin", f_asin}, {"acos", f_acos}, {"atan", f_atan},
    {"sinh", f_sinh}, {"cosh", f_cosh}, {"tanh", f_tanh}, {"sqrt", f_sqrt}, {"cbrt", f_cbrt},
    {"exp", f_exp}, {"ln", f_ln}, {"log", f_log}, {"log2", f_log2}, {"abs", f_abs},
    {"floor", f_floor}, {"ceil", f_ceil}, {"round", f_round},
};
static const struct { const char *n; double (*f)(double, double); } funcs2[] = {
    {"max", g_max}, {"min", g_min}, {"atan2", g_atan2}, {"hypot", g_hypot}, {"pow", g_pow}, {"root", g_root},
};

/* ---------- tabela de símbolos (lista encadeada; "ans" é pré-definido) ---------- */
static Symbol *symtab = NULL;
Symbol *sym_lookup(const char *name)
{
    for (Symbol *s = symtab; s; s = s->next)
        if (strcmp(s->name, name) == 0) return s;
    Symbol *s = calloc(1, sizeof *s);
    s->name = strdup(name); s->next = symtab; symtab = s;
    return s;
}
void sym_define(Symbol *s, double v) { s->value = v; s->defined = 1; }
void sym_list(void)
{
    int n = 0;
    for (Symbol *s = symtab; s; s = s->next)
        if (s->defined) { printf("%s = %.15g\n", s->name, s->value); n++; }
    if (!n) printf("(nenhuma variável definida)\n");
}
double use_var(Symbol *s)
{
    if (!s->defined) return fail("variável '%s' não definida", s->name);
    return s->value;
}

int classify(const char *text)
{
    if (!strcmp(text, "deg"))  return CMD_DEG;
    if (!strcmp(text, "rad"))  return CMD_RAD;
    if (!strcmp(text, "vars")) return CMD_VARS;
    for (size_t i = 0; i < sizeof consts / sizeof *consts; i++)
        if (!strcmp(text, consts[i].n)) { yylval.num = consts[i].v; return CONST; }
    for (size_t i = 0; i < sizeof funcs1 / sizeof *funcs1; i++)
        if (!strcmp(text, funcs1[i].n)) { yylval.f1 = funcs1[i].f; return FUNC1; }
    for (size_t i = 0; i < sizeof funcs2 / sizeof *funcs2; i++)
        if (!strcmp(text, funcs2[i].n)) { yylval.f2 = funcs2[i].f; return FUNC2; }
    yylval.sym = sym_lookup(text);
    return ID;
}

/* ---------- saída ---------- */
void show_result(double v)
{
    if (sem_err) return;
    printf("= %.15g\n", v);
    sym_define(sym_lookup("ans"), v);
}
void set_mode(int deg) { if (!sem_err) { angle_deg = deg; printf("modo: %s\n", deg ? "graus" : "radianos"); } }
void end_stmt(void)
{
    if (sem_err) n_errors++;
    sem_err = 0;
    if (interactive) { printf("> "); fflush(stdout); }
}

const char *token_name(int t)
{
    switch (t) {
    case NUMBER: return "NUMBER"; case CONST: return "CONST"; case FUNC1: return "FUNC1";
    case FUNC2: return "FUNC2"; case ID: return "ID"; case ADD: return "ADD"; case SUB: return "SUB";
    case MUL: return "MUL"; case DIV: return "DIV"; case MOD: return "MOD"; case POW: return "POW";
    case FACT: return "FACT"; case LP: return "LP"; case RP: return "RP"; case COMMA: return "COMMA";
    case ASSIGN: return "ASSIGN"; case SEP: return "SEP"; case BAD: return "BAD";
    case CMD_DEG: return "CMD_DEG"; case CMD_RAD: return "CMD_RAD"; case CMD_VARS: return "CMD_VARS";
    default: return "?";
    }
}
