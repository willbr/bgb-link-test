#include <stdio.h>
#include "forth.h"

int
main(void)
{
    init();

    printf("hello5\n\n");

    while (1) {
        while (next_token())
            eval(token);

        printf("ok\n");
    }

    puts("goodbye");
    return 0;
}

