#include <stdio.h>
#include "forth.h"

void
main(void)
{
    init();

    printf("hello5\n\n");

    while (1) {
        if (!str_cmp(token, "")) {
            printf("# ");
            gets(tib);
            in = tib;
            /*printf("tib: %s\n", tib);*/
        }

        while (next_token())
            eval(token);

        printf("ok\n");
    }
}


