// #include <stdio.h>
#include <gb/gb.h>
#include <gb/bgb_emu.h>

unsigned char rbyte = 0;
unsigned short rshort = 0;

void recv_byte(void);
void recv_short(void);
void send(uint8_t n);

typedef void void_fn(void);

void
main(void) {
    static unsigned char command = 0;
    static unsigned char *p;
    static unsigned char c;
    static void_fn *fn;

    BGB_MESSAGE("");
    BGB_MESSAGE("ctif build: $02");
    BGB_MESSAGE("");

    for (;;) {
        if (_io_status == IO_ERROR)
            BGB_printf("io_error\n");

        BGB_printf("> ");

        recv_byte();
        command = rbyte;
        switch (command) {
            case 0: // hack to ignore null char
                BGB_printf(".");
                break;

            case 1: // 1 @ fetch
                recv_short();
                p = (unsigned char *)rshort;

                BGB_printf("@ $%hx $%x\n", command, p);
                BGB_printf("addr: $%x\n", p);
                BGB_printf("val:  $%hx\n\n", *p);
                send(*p);
                break;

            case 2: // 2 ! set
                recv_short();
                p = (unsigned char *)rshort;
                recv_byte();

                BGB_printf("! $%hx $%x $%hx\n", command, p, rbyte);

                BGB_printf("addr: $%x\n", p);

                BGB_printf("before: $%hx\n", *p);

                *p = rbyte;
                BGB_printf("after: $%hx\n\n", *p);
                break;

            case 3: // 3 call
                recv_short();
                fn = (void_fn)rshort;

                BGB_printf("call $%hx $%x\n", command, fn);

                BGB_printf("addr: $%x\n\n", fn);

                (*fn)();
                break;

            default:
                BGB_printf("unknown command: $%x\n", command);
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
            BGB_printf("io isn't idle\n");
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

void
send(uint8_t n) {
    _io_out = n;

    send_byte();

    while (_io_status == IO_SENDING);

    if (_io_status != IO_IDLE) {
        BGB_printf("\nsend_byte failed\n");
    }
}

