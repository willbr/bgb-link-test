#include <stdint.h>
#include <stdlib.h> // exit

typedef void (c_func)(void);
typedef uint8_t  u8;
typedef uint16_t u16;

struct dict_elem {
    char *name;
    c_func *fn;
    struct dict_elem *next ;
    u16 *code;
};


char memory[0x400] = {0};

u16 *param_stack  = (u16*)&memory[0x300];
char *tib           = NULL;
char *in            = &memory[0x200];
char token[64]     = {0};

char *here         = &memory[0];
struct dict_elem *dict = NULL;
u16 *param_ptr = NULL;

void init(void);
void eval(const char * const token);

void push_param(u16 s);
u16  pop_param(void);
u16  tos(void);

void die2(const char * const msg, const char * const file_name, const int line_number, const char * const func_name);
#define die(msg) die2(msg, __FILE__, __LINE__, __func__)

struct dict_elem* lookup(const char *name);
struct dict_elem* define(char *name, c_func *code);

void* alloc(size_t size);
char * alloc_string(const char const *value);

u8   str_len(const char const *s);
void str_cpy(char *dst, const char const *src);
u8   str_cmp(const char const *s1, const char const *s2);
u16  str_to_u16(const char *str, char **endptr);

void print_dictionary(void);

void fn_add(void);
void fn_sub(void);
void fn_mult(void);
void fn_div(void);
void fn_print(void);
void fn_print_stack(void);

void fn_dup(void);


void
init(void)
{
    param_ptr = param_stack;
    tib       = &memory[0x200];
    in        = &memory[0x200];

    define("+",  fn_add);
    define("-",  fn_sub);
    define("*",  fn_mult);
    define("/",  fn_div);
    define(".",  fn_print);
    define(".s", fn_print_stack);

    define("dup", fn_dup);

    /*print_dictionary();*/
}


void
eval(const char * const token)
{
    u16 s = 0;
    char *endp = NULL;
    struct dict_elem *elem = NULL;
    c_func *fn = NULL;

    /*printf("eval token: %s\n", token);*/

    if (*token == '\0')
        die("null char");

    if (*token == '"')
        die("double quote char");

    s = str_to_u16(token, &endp);
    /*printf("s: %d\n", s);*/

    if (endp == NULL)
        die("endp is NULL");

    if (*endp == '\0') { 
        push_param(s);
        return;
    }

    elem = lookup(token);
    if (elem == NULL) {
        fprintf(stderr, "token: '%s'\n", token);
        die("word not found");
    }

    /*printf("dict elem: %s\n", elem->name);*/

    fn = elem->fn;
    if (fn == NULL)
        die("missing function pointer");

    fn();
}


void
die2(const char * const msg, const char * const file_name, const int source_line_number, const char * const func_name)
{
    printf("\nDIE: %s\n\n", msg);
    /*fprintf(stderr, "%3d: %s", line_number, buffer);*/
    /*fprintf(stderr, "     %*s^\n\n", i, "");*/
    printf("%s : %d : %s\n\n", file_name, source_line_number, func_name);
    exit(1);
}


void
push_param(u16 s)
{
    *param_ptr = s;
    param_ptr += 1;
}


u16
pop_param(void)
{
    param_ptr -= 1;
    return *param_ptr;
}


struct dict_elem*
lookup(const char *name)
{
    struct dict_elem *elem = dict;
    /*printf("lookup: %s\n", name);*/

    while (elem) {
        /*printf("lookup elem: %p\n", elem);*/
        if (elem->name == NULL)
            die("missing name");

        /*printf("lookup elem->name: %s\n", elem->name);*/

        if (!str_cmp(elem->name, name))
            return elem;

        elem = elem->next;
    }

    return NULL;
}


struct dict_elem*
define(char *name, c_func *fn)
{
    struct dict_elem *new = alloc(sizeof(struct dict_elem));
    char *new_name = alloc(str_len(name) + 1);

    str_cpy(new_name, name);

    new->name = new_name;
    new->fn = fn;
    new->next = dict;

    return dict = new;
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


u8
next_token(void)
{
    char *t = token;
    char *start_pos = NULL;

    while (*in == ' ')
        in++;

    start_pos = in;

    while (*in != '\0' && *in != ' ' && *in != '\n')
        *t++ = *in++;

    *t = '\0';
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
print_dictionary(void)
{
    struct dict_elem *elem = dict;

    printf("dict\n");
    while (elem) {
        if (elem->name == NULL)
            die("missing name");
        printf("    %s\n", elem->name);

        elem = elem->next;
    }
    printf("\n");
}

