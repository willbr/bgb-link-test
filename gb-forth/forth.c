#include <stdio.h>
#include "forth.h"

int
main(void)
{
    init();

    printf("hello5\n\n");

    while (1) {
        if (!str_cmp(token, "")) {
            printf("# ");
            if (fgets(tib, 64, stdin) == NULL)
                return 0;
            in = tib;
            /*printf("tib: %s\n", tib);*/
        }

        while (next_token())
            eval(token);

        printf("ok\n");
    }
}


