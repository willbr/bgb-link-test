#include <stdio.h>
#include <stdint.h>
#include <gb/gb.h>

uint8_t read_byte(void) ;
void byte_loop(void) ;
void string_loop(void) ;

char tib[64] = "\0";
char *s = tib;
char c = '\0';

void
main(void) {
    char cmd = 0;

    printf("hello4\n\n");

    cmd = read_byte();

    switch (cmd) {
        case 1:
            byte_loop();
            break;

        case 2:
            string_loop();
            break;

        default:
            printf("unknown cmd: %d\n", cmd);
    }
}


void
byte_loop(void) {
    while (1) {
        c = read_byte();
        printf("%x ", c);
    }
}


void
string_loop(void) {
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
            printf("string_loop failed");
        }
    }
}

uint8_t
read_byte(void) {
    receive_byte();

    while (_io_status == IO_RECEIVING);

    if (_io_status != IO_IDLE) {
        printf("read_byte failed\n");
    }

    return _io_in;
}
