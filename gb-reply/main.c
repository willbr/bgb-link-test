#include <stdio.h>
#include <stdint.h>
#include <gb/gb.h>

uint8_t read_byte(void) ;
void    send(uint8_t);

char c = '\0';

void
main(void) {
    char cmd = 0;

    printf("reply + 1\n\n");

    for (;;) {
        c = read_byte();
        c += 1;
        printf("%hx ", c);
        send(c);
    }

}


uint8_t
read_byte(void) {
    receive_byte();

    while (_io_status == IO_RECEIVING);

    if (_io_status != IO_IDLE) {
        printf("\nread_byte failed\n");
    }

    return _io_in;
}

void
send(uint8_t n) {
    _io_out = n;

    send_byte();

    while (_io_status == IO_SENDING);

    if (_io_status != IO_IDLE) {
        printf("\nsend_byte failed\n");
    }
}
