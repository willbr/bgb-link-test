#include <stdio.h>
#include <gb/gb.h>

char tib[64] = "\0";

void
main(void) {
    char *s = tib;

    printf("hello3\n\n");

    while (1) {
        receive_byte();
        while (_io_status == IO_RECEIVING);
        if (_io_status == IO_IDLE) {
            *s++ = _io_in;
            if (_io_in == '\0') {
                s = tib;
                printf("%s\n", tib);
            }

        } else {
            printf("error ");
        }
    }
}

