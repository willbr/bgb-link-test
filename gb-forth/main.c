#include <stdio.h>
#include <gb/gb.h>

typedef void (c_func)(void);

struct dict_elem {
    char *name;
    c_func *fn;
    struct dict_elem *next ;
};

char memory[0x400] = {0};
/*char *token = NULL;*/
/*FILE *f_input = NULL;*/
short *param_stack  = (short*)&memory[0x300];
char *tib          = &memory[0x200];
short *return_stack = (short*)&memory[0x3ff];
/*char *input        = &memory[0xf000];*/
/*char *input_head   = &memory[0xf000];*/
/*char *input_tail   = &memory[0xf000];*/
/*char *input_end    = &memory[0xfa00];*/
char *here         = &memory[0];
struct dict_elem *dict = NULL;
short *param_ptr = NULL;

void init(void);
/*void push_token(char *t);*/
void push_param(short s);
short pop_param(void);
void eval(const char * const token);
void die2(const char * const msg, const char * const file_name, const int line_number, const char * const func_name);
#define die(msg) die2(msg, __FILE__, __LINE__, __func__)
struct dict_elem* lookup(const char *name);
struct dict_elem* define(char *name, c_func *code);
void* alloc(size_t size);
char * alloc_string(char *value);

int strlen(const char const *s);
void strcpy(char *dst, const char const *src);
int strcmp(const char const *s1, const char const *s2);
short str_to_short(const char *str, char **endptr);

void fn_add(void);
void fn_print_stack(void);




void
recv(void)
{
    char *s = tib;

    for (;;) {
        receive_byte();
        while (_io_status == IO_RECEIVING);
        if (_io_status == IO_IDLE) {
            *s++ = _io_in;
            if (_io_in == '\0') {
                return;
            }

        } else {
            printf("error ");
        }
    }
}


void
main(void)
{
    init();

    printf("hello4\n\n");

    while (1) {
        printf("# ");
        recv();
        printf("%s\n", tib);
        eval(tib);
        printf("ok\n");
    }
}


void
init(void)
{
    printf("&memory: $%x\n", memory);
    printf("&param_stack: $%x\n", param_stack);

    param_ptr = param_stack;

    define("+",  fn_add);
    define(".s", fn_print_stack);
}


void
eval(const char * const token)
{
    short s = 0;
    char *endp = NULL;
    struct dict_elem *elem = NULL;
    c_func *fn = NULL;

    /*printf("eval token: %s\n", token);*/

    if (*token == '\0')
        die("null char");

    if (*token == '"')
        die("double quote char");

    s = str_to_short(token, &endp);
    /*printf("s: %d\n", s);*/

    if (endp == NULL)
        die("endp is NULL");

    if (*endp == '\0') { 
        push_param(s);
        return;
    }

    elem = lookup(token);
    if (elem == NULL)
        die("word not found");

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
}


void
push_param(short s)
{
    /*printf("push %d\n", s);*/
    *param_ptr = s;
    param_ptr += 1;
}


short
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

        if (!strcmp(elem->name, name))
            return elem;

        elem = elem->next;
    }

    return NULL;
}


struct dict_elem*
define(char *name, c_func *fn)
{
    struct dict_elem *new = alloc(sizeof(struct dict_elem));
    char *new_name = alloc(strlen(name) + 1);

    strcpy(new_name, name);

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
strcpy(char *dst, const char const *src)
{
    while (*src != '\0') {
        *dst++ = *src++;
    }
    *dst = '\0';
}


int
strlen(const char const *s)
{
    int i = 0;
    while (*s != '\0') {
        i++;
        s++;
    }
    return i;
}


int
strcmp(const char const *s1, const char const *s2)
{
    int i = 0;
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
    char *new_string = alloc(strlen(value) + 1);
    strcpy(new_string, value);
    return new_string;
}


short
str_to_short(const char *str, char **endptr)
{
    short r = 0;
    short i = 0;
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
    short n2 = pop_param();
    short n1 = pop_param();
    short rval = n1 + n2;
    push_param(rval);
}


void
fn_print_stack(void)
{
    short *param_head = param_stack;
    printf("stack: ", *param_head);
    while (param_head < param_ptr) {
        printf("%d ", *param_head);
        param_head += 1;
    }
    printf("\n");
}

