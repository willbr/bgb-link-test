# https://bgb.bircd.org/bgblink.html

from dataclasses import dataclass
from multiprocessing import Process, Pipe
from struct import pack, unpack
from enum import IntEnum
import socket


class bgb_cmd(IntEnum):
    version = 1
    joypad  = 101
    sync1   = 104
    sync2   = 105
    sync3   = 106
    status  = 108


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
            return f"joypad {str(joy(self.b2))}"
        elif self.cmd == bgb_cmd.sync1:
            return f"sync1 ${self.b2:x}"
        elif self.cmd == bgb_cmd.sync2:
            return f"sync2 ${self.b2:x}"
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


sock = None
timestamp = 0
remote_timestamp = 0


def init():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect(('localhost', 8765))


def send(msg):
    data = pack("<BBBBI", msg.cmd, msg.b2, msg.b3, msg.b4, timestamp)
    print(' s', msg)
    cnt = sock.send(data)
    assert cnt == 8


def send_msg(cmd, b2, b3, b4):
    send(BGBMessage(cmd, b2, b3, b4))


def recv():
    global remote_timestamp

    data = sock.recv(8)
    if len(data) == 0:
        return None

    *reply, remote_timestamp = unpack("<BBBBI", data)
    msg = BGBMessage(*reply)
    if msg.cmd not in [bgb_cmd.sync3]:
        print('r', msg)

    return msg


def parse_stdio(msg):
    return BGBMessage(bgb_cmd.sync1, 0xff, 0b1000_0001, 0)


def link_client(conn):
    global timestamp

    init()
    while True:
        if conn.poll():
            msg = conn.recv()
            send(parse_stdio(msg))
            #conn.send(['hi', msg])

        msg = recv()
        if msg == None:
            continue

        cmd = msg.cmd

        if cmd == bgb_cmd.version:
            send_msg(bgb_cmd.version, 1, 4, 0)
        elif cmd == bgb_cmd.joypad:
            pass
        elif cmd == bgb_cmd.status:
            send(msg)
        elif cmd == bgb_cmd.sync1:
            pass
        elif cmd == bgb_cmd.sync2:
            conn.send('oi')
            pass
        elif cmd == bgb_cmd.sync3:
            if b2 == 0:
                timestamp = remote_timestamp
        else:
            print('r', cmd, b2, b3, b4)
            assert False, cmd

        timestamp = remote_timestamp


def main():
    parent_conn, child_conn = Pipe()
    p = Process(target=link_client, args=(child_conn,))
    p.start()
    print(parent_conn.recv())
    while True:
        line = input("# ")
        parent_conn.send(line)
        print(parent_conn.recv())
    # p.join()

if __name__ == '__main__':
    main()

