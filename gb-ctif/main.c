#include <stdio.h>
#include <gb/gb.h>

unsigned char rbyte = 0;
unsigned short rshort = 0;

void recv_byte(void);
void recv_short(void);
typedef void void_fn(void);

void
main(void) {
    static unsigned char command = 0;
    static unsigned char *p;
    static unsigned char c;
    static void_fn *fn;

    printf("ctif\n\n");

    for (;;) {
        if (_io_status == IO_ERROR)
            printf("io_error\n");

        printf("> ");

        recv_byte();
        command = rbyte;
        switch (command) {
            case 0: // hack to ignore null char
                printf(".");
                break;

            case 1: // 1 @ fetch
                recv_short();
                p = (unsigned char *)rshort;

                printf("%d $%x\n", command, p);
                printf("fetch:\n");
                printf("addr: $%x\n", p);
                printf("val:  $%x\n\n", *p);

                break;

            case 2: // 2 ! set
                recv_short();
                p = (unsigned char *)rshort;
                recv_byte();

                printf("%d $%x $%x\n", command, p, rbyte);

                printf("store\n");
                printf("addr: $%x\n", p);

                printf("before: $%x\n", *p);

                *p = rbyte;
                printf("after: $%x\n\n", *p);
                break;

            case 3: // 3 call
                recv_short();
                fn = (void_fn)rshort;

                printf("%d $%x\n", command, fn);

                printf("call:\n");
                printf("addr: $%x\n\n", fn);

                (*fn)();
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
            printf("io isn't idle\n");
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

