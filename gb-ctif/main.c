#include <stdio.h>
#include <gb/gb.h>

unsigned char rbyte = 0;
unsigned short rshort = 0;

void recv_byte(void);
void recv_short(void);

void
main(void) {
    static unsigned char command = 0;
    static unsigned char *p;
    static unsigned char c;

    printf("ctif\n\n");

    for (;;) {
        // wait_vbl_done();
        recv_byte();
        command = rbyte;
        switch (command) {
            case 0:
                break;

            case 1: // 1 @ fetch
                printf("fetch: %d\n", command);

                recv_short();
                p = (unsigned char *)rshort;
                printf("addr: $%x\n", p);

                printf("val: $%x\n", *p);
                break;

            case 2: // 2 ! set
                printf("store command: %d\n", command);

                recv_short();
                p = (unsigned char *)rshort;
                printf("addr: $%x\n", p);

                recv_byte();
                printf("val: $%x\n", *p);

                *p = rbyte;
                printf("val: $%x\n", *p);
                break;

            case 3: // 3 c call
                printf("call command: %d\n", command);
                recv_short();
                printf("addr: $%x\n", rshort);
                break;

            default:
                printf("unknown command: $%x\n", command);
                break;
        }
    }
}


void
recv_byte(void) {
    while (1) {
        receive_byte();
        while (_io_status == IO_RECEIVING);
        if (_io_status == IO_IDLE) {
            rbyte = _io_in;
            return;
        } else {
            printf("error\n");
        }
    }
}

void
recv_short(void) {
    static unsigned char low;
    static unsigned char high;
    recv_byte();
    high = rbyte;
    recv_byte();
    low = rbyte;
    rshort = (high << 8) + low;
}

