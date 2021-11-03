# https://bgb.bircd.org/bgblink.html

from dataclasses import dataclass
from multiprocessing import Process, Pipe
from struct import pack, unpack
from enum import IntEnum
import socket


sock = None
timestamp = 0

class bgb_cmd(IntEnum):
    version = 1   # 0x01
    joypad  = 101 # 0x65
    sync1   = 104 # 0x68
    sync2   = 105 # 0x69
    sync3   = 106 # 0x6a
    status  = 108 # 0x6c
    want    = 109 # 0x6d


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


    def __repr__(self):
        return "asdf"


    def __str__(self):
        if self.cmd == bgb_cmd.version:
            return f"version {self.b2}.{self.b3}"
        elif self.cmd == bgb_cmd.joypad:
            pressed = self.b2 & 0b1000
            return f"joypad {str(joy(self.b2))} {pressed=}"
        elif self.cmd == bgb_cmd.sync1:
            return f"sync1 ${self.b2:x}, {self.b2}, {escape(self.b2)}"
        elif self.cmd == bgb_cmd.sync2:
            return f"sync2 ${self.b2:x}, {self.b2}, {escape(self.b2)}"
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
        else:
            return f"unknown: ${cmd:x} ${b2:x} ${b3:x} ${b4:x}"


def escape(i):
    c = chr(i)
    return c

def init():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect(('localhost', 8765))


def send(msg):
    data = pack("<BBBBI", msg.cmd, msg.b2, msg.b3, msg.b4, timestamp)
    if msg.cmd not in [bgb_cmd.sync3]:
        print('s', msg)
    cnt = sock.send(data)
    assert cnt == 8


def send_msg(cmd, b2=None, b3=None, b4=None):

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

    send(BGBMessage(cmd, b2, b3, b4))


def recv():
    global timestamp

    data = sock.recv(8)
    if len(data) == 0:
        return None

    *reply, i1 = unpack("<BBBBI", data)
    if i1:
        timestamp = i1 + 1
        timestamp &= 0b_01111111_11111111_11111111_11111111
    msg = BGBMessage(*reply)
    if msg.cmd not in [bgb_cmd.sync3, bgb_cmd.joypad]:
        print(' r', msg)

    return msg


def link_client(conn):
    init()
    msgs = []
    send_buffer = []
    recv_buffer = []
    ready = True
    retry = False
    c = None

    while True:
        if conn.poll():
            line = conn.recv()
            msgs.append(line)
            print(f"{send_buffer=} {msgs=} {ready=}")

        if retry:
            print(f"{c=} {send_buffer=} {msgs=} {ready=}")
            send_msg(bgb_cmd.sync1, c)
            retry = False
        elif send_buffer and ready:
            c = send_buffer.pop(0)
            print(f"{c=} {send_buffer=} {msgs=} {ready=}")
            send_msg(bgb_cmd.sync1, c)
            ready = False
        elif len(send_buffer) == 0 and msgs:
            line = msgs.pop(0)
            send_buffer = list(line.encode()) + [0]
            print(f"{send_buffer=}")

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
                print(line)
            else:
                recv_buffer.append(msg.b2)
            send_msg(bgb_cmd.sync2)
        elif cmd == bgb_cmd.sync2:
            if msg.b2 == 0x66:
                retry = True
            else:
                retry = False
                ready = True
        elif cmd == bgb_cmd.sync3:
            send(msg)
        else:
            print('r', msg)
            assert False, cmd


def main():
    parent_conn, child_conn = Pipe()
    p = Process(target=link_client, args=(child_conn,))
    p.start()

    try:
        while True:
            line = input("# ")
            parent_conn.send(line)
    except KeyboardInterrupt:
        p.terminate()


if __name__ == '__main__':
    main()

