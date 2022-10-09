#include <stdint.h> /* uint8_t */
#include <stdlib.h> /* exit */

/*
 *
 *
    create
    does>
    ,
    allot
    swap
    immediate

    if
    then
    do

    loop
    here

    literal

    ] colon compiler
    [

    postpone
 */

typedef void (c_func)(void);
typedef unsigned int uint;
typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

struct dict_elem {
    struct dict_elem *prev ;
    char *name;
    u8 immediate;
    c_func *fn;
    u16 *code;
};


enum {
    true  = -1,
    false =  0
};


char memory[0x10000] = {0};

u16 *param_stack = (u16*)&memory[0x5000];
char *tib        = NULL;
char *in         = NULL;
char token[64]   = {0};

char *here         = NULL;
struct dict_elem *latest = NULL;
u16 *param_ptr = NULL;
u8 compiling   = false;

u16 lit  = 0;
u16 next = 0;

void init(void);
void eval(const char * const token);

void push_param(u16 s);
u16  pop_param(void);
u16  tos(void);

#define ESC "\x1b"
#define RED_TEXT "31"
#define YELLOW_TEXT "33"
#define RESET ESC "[0m"

void die2(const char * const msg, const char * const file_name, const int line_number, const char * const func_name);
#define die(msg) die2(msg, __FILE__, __LINE__, __func__)
void ere2(const char * const file_name, const int line_number, const char * const func_name);
#define ere ere2(__FILE__, __LINE__, __func__)

struct dict_elem* lookup(const char *name);
u16 define(char *name, c_func *code, u8 immediate);

void* alloc(size_t size);
char * alloc_string(const char const *value);

u8   str_len(const char const *s);
void str_cpy(char *dst, const char const *src);
u8   str_cmp(const char const *s1, const char const *s2);
u16  str_to_u16(const char *str, char **endptr);

void decompile(struct dict_elem *elem);
void print_dictionary(void);

void fn_next(void);

void fn_add(void);
void fn_sub(void);
void fn_mult(void);
void fn_div(void);

void fn_emit(void);
void fn_print(void);
void fn_print_stack(void);

void fn_colon(void);
void fn_semicolon(void);

void fn_dup(void);
void fn_drop(void);
void fn_swap(void);

void fn_lit(void);
void fn_comma(void);

u8 next_token(void);


void
init(void)
{
    param_ptr = param_stack;
    here      = &memory[0x0000];
    latest    = NULL;
    tib       = &memory[0x4000];
    in        = &memory[0x4000];
    *in       = '\0';

    define("next",  fn_next,  false);

    define("+",  fn_add,  false);
    define("-",  fn_sub,  false);
    define("*",  fn_mult, false);
    define("/",  fn_div,  false);

    define("emit", fn_emit,        false);
    define(".",    fn_print,       false);
    define(".s",   fn_print_stack, false);

    define("dup", fn_dup,   false);
    define("drop", fn_drop, false);
    define("swap", fn_swap, false);

    lit = define("lit", fn_lit, false);
    define(",",   fn_comma, false);

    define(":", fn_colon,     false);
    define(";", fn_semicolon, true);

    /*print_dictionary();*/
}


void
eval(const char * const token)
{
    u16 s = 0;
    char *endp = NULL;
    struct dict_elem *elem = NULL;
    c_func *fn = NULL;

    printf("%s: '%s'\n",
            compiling ? "compile" : "eval",
            token);

    if (*token == '\0')
        die("null char");

    if (*token == '"')
        die("double quote char");

    s = str_to_u16(token, &endp);
    /*printf("s: %d\n", s);*/

    if (endp == NULL)
        die("endp is NULL");

    if (*endp == '\0') { 
        if (compiling) {
            /*printf("%s\n", token);*/
            push_param(lit);
            fn_comma();
            push_param(s);
            fn_comma();
        } else {
            push_param(s);
        }
        return;
    }

    elem = lookup(token);
    if (elem == NULL) {
        fprintf(stderr, "token: '%s'\n", token);
        die("word not found");
    }

    /*printf("dict elem: %s\n", elem->name);*/

    fn = elem->fn;

    if (compiling && !elem->immediate) {
        ptrdiff_t poffset = (void*)elem - (void*)&memory[0];
        u16 offset = poffset;
        push_param(offset);
        fn_comma();
        return;
    }

    if (fn) {
        fn();
        return;
    }

    fprintf(stderr, "dict elem: %s\n", elem->name);

    if (elem->code == NULL)
        die("no code");

    /*print_dictionary();*/
    decompile(elem);
    die("todo");
}


void
die2(const char * const msg, const char * const file_name, const int source_line_number, const char * const func_name)
{
    fprintf(stderr, "\n" ESC "[" RED_TEXT "m" "DIE: %s\n\n", msg);
    fprintf(stderr, "%s : %d : %s\n\n" RESET, file_name, source_line_number, func_name);
    exit(1);
}


void
ere2(const char * const file_name, const int source_line_number, const char * const func_name)
{
    fprintf(stderr,
            ESC "[" YELLOW_TEXT "m%s %d %s" RESET "\n",
            func_name, source_line_number, file_name);
}


void
push_param(u16 s)
{
    /*printf("pushing 0x%03x\n", s);*/
    *param_ptr = s;
    param_ptr += 1;
}


u16
pop_param(void)
{
    if (param_ptr <= param_stack)
        die("underflow");

    param_ptr -= 1;
    /*printf("popping 0x%03x\n", *param_ptr);*/
    return *param_ptr;
}


struct dict_elem*
lookup(const char *name)
{
    struct dict_elem *elem = latest;
    /*printf("lookup: '%s'\n", name);*/

    while (elem) {
        /*printf("lookup elem: %p\n", elem);*/
        if (elem->name == NULL)
            die("missing name");

        /*printf("lookup elem->name: %s\n", elem->name);*/

        if (!str_cmp(elem->name, name))
            return elem;

        elem = elem->prev;
    }

    puts("fail");
    return NULL;
}


u16
define(char *name, c_func *fn, u8 immediate)
{
    u16 offset = here - &memory[0];
    struct dict_elem *new = alloc(sizeof(struct dict_elem));
    char *new_name = alloc(str_len(name) + 1);

    str_cpy(new_name, name);
    /*printf("define name: '%s'\n", name);*/

    new->name = new_name;
    new->prev = latest;
    new->immediate = immediate;

    if (fn) {
        new->fn = fn;
        new->code = NULL;
    } else {
        new->fn = NULL;
        new->code = (u16*)here;
    }

    latest = new;

    return offset;
}


void*
alloc(size_t size)
{
    void *rval = here;
    here += size;
    return rval;
}


void
str_cpy(char *dst, const char const *src)
{
    while (*src != '\0') {
        *dst++ = *src++;
    }
    *dst = '\0';
}


u8
str_len(const char const *s)
{
    u8 i = 0;
    while (*s != '\0') {
        i++;
        s++;
    }
    return i;
}


u8
str_cmp(const char const *s1, const char const *s2)
{
    u8 i = 0;
    while ((*s1 != '\0') && (*s1 == *s2)) {
        s1++;
        s2++;
    }
    if (*s1 < *s2) {
        return -1;
    } else if (*s1 == *s2) {
        return 0;
    } else {
        return 1;
    }
}


char *
alloc_string(const char const *value)
{
    char *new_string = alloc(str_len(value) + 1);
    str_cpy(new_string, value);
    return new_string;
}


u16
str_to_u16(const char *str, char **endptr)
{
    u16 r = 0;
    u16 i = 0;
    while (*str >= '0' && *str <= '9') {
        r = (r * 10) + (*str - '0');
        str += 1;
    }

    if (endptr)
        *endptr = (char*)str;

    if (*str != '\0')
        return 0;
    else 
        return r;
}


void
fn_next(void)
{
    return;
}


void
fn_add(void)
{
    u16 n2 = pop_param();
    u16 n1 = pop_param();
    u16 rval = n1 + n2;
    push_param(rval);
}

void
fn_sub(void)
{
    u16 n2 = pop_param();
    u16 n1 = pop_param();
    u16 rval = n1 - n2;
    push_param(rval);
}

void
fn_mult(void)
{
    u16 n2 = pop_param();
    u16 n1 = pop_param();
    u16 rval = n1 * n2;
    push_param(rval);
}


void
fn_div(void)
{
    u16 n2 = pop_param();
    u16 n1 = pop_param();
    u16 rval = n1 / n2;
    push_param(rval);
}


void
fn_print(void)
{
    u16 n = pop_param();
    printf("print: %d ", n);
}


void
fn_print_stack(void)
{
    u16 *param_head = param_stack;
    printf("stack: ", *param_head);
    while (param_head < param_ptr) {
        printf("%d ", *param_head);
        param_head += 1;
    }
    printf("\n");
}


void
fn_dup(void)
{
    push_param(tos());
}


void
fn_drop(void)
{
    pop_param();
}


void
fn_swap(void)
{
    u16 temp1 = pop_param();
    u16 temp2 = pop_param();
    push_param(temp1);
    push_param(temp2);
}


void
fn_lit(void)
{
    die("todo");
}


void
fn_comma(void)
{
    u16 *a = (u16*)here;
    *a++ = pop_param();
    here = (u8*)a;
}


void
fn_emit(void)
{
    putchar(pop_param() & 0xff);
}


void
fn_colon(void)
{
    next_token();
    define(token, NULL, false);
    compiling = true;
}


void
fn_semicolon(void)
{
    push_param(next);
    fn_comma();
    compiling = false;
}


u8
next_token(void)
{
    char *t = token;
    char *start_pos = NULL;

    if (!*in) {
        if (fgets(in, 64, stdin) == NULL) {
            if (*in == EOF)
                die("EOF");
            return 0;
        }
    }

    /*printf("%p\n", in);*/
    /*printf("%d\n", *in);*/
    /*printf("%c\n", *in);*/
    /*printf("%s\n", in);*/
    /*die("todo");*/

    while (*in == ' ' || *in == '\n')
        in++;

    start_pos = in;

    while (*in != '\0' && *in != ' ' && *in != '\n')
        *t++ = *in++;

    /*sleep(1000);*/
    *t = '\0';
    /*printf("%p\n", in);*/
    /*printf("token: %s\n", token);*/
    /*die("todo");*/
    return start_pos != in;
}


u16
tos(void)
{
    if (param_ptr <= param_stack)
        die("stack underflow");
    return *(param_ptr - 1);
}


void
decompile(struct dict_elem *elem)
{
    u16 *cp = elem->code;
    struct dict_elem *code = NULL;

    printf(": %s ", elem->name);
    for (;*cp != next; cp += 1) {
        code = (void*)&memory[0] + *cp;
        if (*cp == lit) {
            cp += 1;
            printf("%d", *cp);
        } else {
            /*printf("name: '%s', 0x%03x\n", code->name, *cp);*/
            printf("%s", code->name);
        }

        printf(" ");
    }

    printf(";\n");
}


void
print_dictionary(void)
{
    struct dict_elem *elem = latest;

    if (elem)
        printf("dict\n");
    else
        printf("dict is empty\n");

    while (elem) {
        printf("    ");

        u16 offset = (void*)elem - &memory[0];
        printf("0x%03x, ", offset);

        if (elem->name == NULL)
            die("missing name");
        printf("%s\n", elem->name);

        elem = elem->prev;
    }
    printf("\n");
}

