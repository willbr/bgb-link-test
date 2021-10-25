import socket
import sys
import struct
from enum import IntEnum
from time import sleep
from random import random

class joy(IntEnum):
    RIGHT = 0
    LEFT = 1
    UP = 2
    DOWN = 3
    A = 4
    B = 5
    SELECT = 6
    START = 7

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sock.connect(('localhost', 8765))

timestamp = 0

def next():
    data = sock.recv(8)
    if len(data) == 0:
        return None
    #print(f"next {data=}")
    *reply, remote_timestamp = struct.unpack("<BBBBI", data)
    #print(f"next {reply=}, {timestamp=}")
    return reply


def send(cmd, b2, b3, b4):
    data = struct.pack("<BBBBI", cmd, b2, b3, b4, timestamp)
    #print(f"sending {data=}")
    print(f"\tsending {cmd=} {b2=} {b3=} {b4=}")
    cnt = sock.send(data)
    assert cnt == 8


def press_joy(button):
    b2 = 0b00001000 | button
    send(101,b2,0,0)


def release_joy(button):
    send(101,button,0,0)


def click_joy(button):
    press_joy(button)
    sleep(0.5)
    release_joy(button)

def joy_test():
    for i in range(8):
        release_joy(i)

    for b in joy:
        print(b)
        press_joy(b)
        sleep(0.5 + random())
        release_joy(b)

    sleep(1)

    for i in range(8):
        release_joy(i)


def bitflags(byte):
    f0 = (byte & 0b00000001) != 0
    f1 = (byte & 0b00000010) != 0
    f2 = (byte & 0b00000100) != 0
    f3 = (byte & 0b00001000) != 0
    f4 = (byte & 0b00010000) != 0
    f5 = (byte & 0b00100000) != 0
    f6 = (byte & 0b01000000) != 0
    f7 = (byte & 0b10000000) != 0
    return f7, f6, f5, f4, f3, f2, f1, f0

handshake = b'\x01\x01\x04\x00\x00\x00\x00\x00'
handshake = 0x01_01_04_00_00000000

try:
    handshake = next()
    send(*handshake)

    #joy_test()

    # send(104, 64, 0, 0)
    #send(105, 64, 0, 0)
    #click_joy(joy.B)

    while 1:
        r = next()

        if r == None:
            #print(".", end="")
            continue

        #print(r)

        cmd, b2, b3, b4 = r

        if cmd == 1: # version
            print("version", r)
        elif cmd == 101: # joypad
            print("joypad", r)
        elif cmd == 104: # sync 1, send a byte as master
            print("sync1")
            f7, f6, f5, f4, f3, double_speed, high_speed, f0 = bitflags(b3)
            print(f"{double_speed=} {high_speed=}")
        elif cmd == 105: # sync 2, send a byte as slave
            print("sync2", r)
            send(*r)
        elif cmd == 106: # sync 3, reply or sync
            print("sync3", r)
        elif cmd == 108: # status
            *_, supportreconnect, paused, running = bitflags(b2)
            print(f"{supportreconnect=} {paused=} {running=}")
            send(*r)
        elif cmd == 109: # wantdisconnect
            print("wantdisconnect", r)
        else:
            raise ValueError





    
finally:
    print('closing socket')
    sock.close()
