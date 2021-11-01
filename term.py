# https://bgb.bircd.org/bgblink.html

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


sock = None
reply = None
timestamp = 0
remote_timestamp = 0
cmd = b2 = b3 = b4 = 0


def init():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect(('localhost', 8765))


def send(s1, s2, s3, s4):
    global cmd, b2, b3, b4
    cmd, b2, b3, b4 = s1, s2, s3, s4
    data = pack("<BBBBI", cmd, b2, b3, b4, timestamp)
    # if cmd not in [bgb_cmd.status]:
        # print(' s', msgstr(cmd, b2, b3, b4))
    print(' s', msgstr())
    cnt = sock.send(data)
    assert cnt == 8


def recv():
    global reply, remote_timestamp
    global cmd, b2, b3, b4

    data = sock.recv(8)
    if len(data) == 0:
        return True

    *reply, remote_timestamp = unpack("<BBBBI", data)
    cmd, b2, b3, b4 = reply
    if cmd not in [bgb_cmd.sync3]:
        print('r', msgstr())


def msgstr():
    if cmd == bgb_cmd.version:
        return f"version {b2}.{b3}"
    elif cmd == bgb_cmd.joypad:
        return f"joypad {str(joy(b2))}"
    elif cmd == bgb_cmd.sync1:
        return f"sync1 ${b2:x}"
    elif cmd == bgb_cmd.sync2:
        return f"sync2 ${b2:x}"
    elif cmd == bgb_cmd.sync3:
        if b2:
            return "sync3 ack"
        else:
            return "sync3 sync"
    elif cmd == bgb_cmd.status:
        running           = b2 & 0b001
        paused            = b2 & 0b010
        support_reconnect = b2 & 0b100
        return f"status: {running=} {paused=} {support_reconnect=}"
    else:
        return f"unknown: {reply=}"


def parse_stdio(msg):
    return bgb_cmd.sync1, 0xff, 0b1000_0001, 0


def link_client(conn):
    global timestamp

    init()
    while True:
        if conn.poll():
            msg = conn.recv()
            send(*parse_stdio(msg))
            #conn.send(['hi', msg])

        if recv():
            continue

        if cmd == bgb_cmd.version:
            send(bgb_cmd.version, 1, 4, 0)
        elif cmd == bgb_cmd.joypad:
            pass
        elif cmd == bgb_cmd.status:
            send(cmd, b2, b3, b4)
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
    try:
        main()
    except KeyboardInterrupt:
        exit(0)

