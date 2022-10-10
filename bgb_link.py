# https://bgb.bircd.org/bgblink.html

# serial
# https://github.com/gbdk-2020/gbdk-2020/blob/9f55694b6da6c5abcde5150a4454d020aa72a78c/gbdk-lib/libc/targets/gbz80/serial.s

# globals
# https://github.com/gbdk-2020/gbdk-2020/blob/d2f10491ef6e3e9216f73300bfbb2d14cfe5e4bb/gbdk-lib/libc/targets/gbz80/gb/global.s
# ;; Status codes for IO
# .IO_IDLE        = 0x00
# .IO_SENDING     = 0x01
# .IO_RECEIVING   = 0x02
# .IO_ERROR       = 0x04

# ;; Type of IO data
# .DT_IDLE        = 0x66
# .DT_RECEIVING   = 0x55

from dataclasses import dataclass
from struct import pack, unpack
from enum import IntEnum
from time import time
import socket


log  = None
sock = None
timestamp = 0
last_sent = 0

class bgb_cmd(IntEnum):
    version    = 1   # 0x01
    joypad     = 101 # 0x65 'e'
    sync1      = 104 # 0x68 'h'
    sync2      = 105 # 0x69 'i'
    sync3      = 106 # 0x6a 'j'
    status     = 108 # 0x6c 'l'
    disconnect = 109 # 0x6d


class joy(IntEnum):
    right  = 0
    left   = 1
    up     = 2
    down   = 3
    a      = 4
    b      = 5
    select = 6
    start  = 7


@dataclass
class BGBMessage:
    cmd: int = 0
    b2:  int = 0
    b3:  int = 0
    b4:  int = 0
    i1:  int = 0

    def __init__(self, cmd, b2=None, b3=None, b4=None, i1=None):

        if cmd == bgb_cmd.sync1:
            if b3 == None:
                b3 = 0x81
        elif cmd == bgb_cmd.sync2:
            if b2 == None:
                b2 = 0x55
            if b3 == None:
                b3 = 0x80

        if b2 == None:
            b2 = 0
        if b3 == None:
            b3 = 0
        if b4 == None:
            b4 = 0

        self.cmd = cmd
        self.b2  = b2
        self.b3  = b3
        self.b4  = b4
        self.i1  = i1


    def __repr__(self):
        return str(self)


    def __str__(self):
        if self.cmd == bgb_cmd.version:
            return f"version {self.b2}.{self.b3}"
        elif self.cmd == bgb_cmd.joypad:
            pressed = self.b2 & 0b1000
            return f"joypad {str(joy(self.b2))} {pressed=}"
        elif self.cmd == bgb_cmd.sync1:
            return f"sync1 ${self.b2:02x}, {self.b2:3d}, {escape(self.b2)}"
        elif self.cmd == bgb_cmd.sync2:
            return f"sync2 ${self.b2:02x}, {self.b2:3d}, {escape(self.b2)}"
        elif self.cmd == bgb_cmd.sync3:
            if self.b2:
                return "sync3 ack"
            else:
                return "sync3 sync"
        elif self.cmd == bgb_cmd.status:
            running           = self.b2 & 0b001
            paused            = self.b2 & 0b010
            support_reconnect = self.b2 & 0b100
            return f"status: {running=} {paused=} {support_reconnect=}"
        elif self.cmd == bgb_cmd.disconnect:
            return f"disconnect"
        else:
            return f"unknown: ${self.cmd:x} ${self.b2:x} ${self.b3:x} ${self.b4:x}"


def escape(i):
    return repr(chr(i))

def init():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect(('localhost', 8765))


def send(msg):
    global timestamp
    global last_sent

    timestamp += 1
    timestamp &= 0b_11111111_11111111_11111111_01111111

    data = pack("<BBBBI", msg.cmd, msg.b2, msg.b3, msg.b4, timestamp)
    if msg.cmd not in [bgb_cmd.sync3]:
        if log:
            log.send(f"s {msg}")
    cnt = sock.send(data)
    assert cnt == 8
    last_sent = time()


def send_msg(cmd, b2=None, b3=None, b4=None):
    send(BGBMessage(cmd, b2, b3, b4))


def recv():
    global timestamp

    try:
        data = sock.recv(8)
    except BlockingIOError as e:
        return None

    if data == b'':
        return None

    *reply, i1 = unpack("<BBBBI", data)
    # if i1:
        # timestamp = i1
    msg = BGBMessage(*reply)
    if msg.cmd not in [bgb_cmd.sync3, bgb_cmd.joypad]:
        if log:
            log.send(f"r {msg}")

    return msg


def link_client(pipe, log_pipe):
    global log
    log  = log_pipe

    try:
        init()
        pipe.send("connected")
    except ConnectionRefusedError as e:
        pipe.send(f"failed to connect: {e}")
        pipe.recv()
        return

    # initial handshake

    msg = recv()
    assert msg.cmd == bgb_cmd.version
    send_msg(bgb_cmd.version, 1, 4)

    msg = recv()
    assert msg.cmd == bgb_cmd.status
    send(msg)

    sock.setblocking(False)

    msgs = []
    send_buffer = []
    recv_buffer = []
    state = "ready"
    c = None

    def handle_input():
        if pipe.poll():
            line = pipe.recv()
            msgs.append(line)
            # log.send(f"got {line}")

    while True:
        handle_input()

        if state == "send":
            send_msg(bgb_cmd.sync1, c)
            state = "ack?"
        elif send_buffer and state == "ready":
            c = send_buffer.pop(0)
            state = "send"
        elif len(send_buffer) == 0 and msgs:
            line = msgs.pop(0)
            send_buffer = list(line.encode()) + [0]
            log.send(f"{send_buffer=}")
        elif state == "ack?":
            elapsed = time() - last_sent
            if elapsed > 2:
                state = "send"
        else:
            print(f"{state=}")
            pass

        msg = recv()
        if msg == None:
            continue

        cmd = msg.cmd

        if cmd == bgb_cmd.version:
            send_msg(bgb_cmd.version, 1, 4)
        elif cmd == bgb_cmd.joypad:
            pass
        elif cmd == bgb_cmd.status:
            send(msg)
        elif cmd == bgb_cmd.sync1:
            if msg.b2 == 0:
                line = bytearray(recv_buffer).decode('ascii')
                recv_buffer = []
                pipe.send(f"{line=}")
            else:
                recv_buffer.append(msg.b2)
            send_msg(bgb_cmd.sync2)
        elif cmd == bgb_cmd.sync2:
            if msg.b2 == 0x66: # IDLE
                if state == "ack?":
                    state = "send"
                else:
                    log.send(f"what? {state=} {msg=}")
                    send(msg)
            elif msg.b2 == 0x55: # RECEIVING
                if state == "ack?":
                    state = "ready"
                else:
                    log.send(f"what? {state=} {msg=}")
                    send(msg)
            else:
                # log.send(f"what? {state=} {msg=}")
                send(msg)
        elif cmd == bgb_cmd.sync3:
            send(msg)
        elif cmd == bgb_cmd.disconnect:
            log.send("gameboy disconnected")
            return
        else:
            log.send(f"r {msg}")
            assert False, cmd


def handshake(setblocking=False):
    msg = recv()
    assert msg.cmd == bgb_cmd.version
    send_msg(bgb_cmd.version, 1, 4)

    msg = recv()
    assert msg.cmd == bgb_cmd.status
    send(msg)

    sock.setblocking(setblocking)

    return msg

