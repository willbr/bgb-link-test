import socket
import asyncio

from time import perf_counter

from bgb_link import *


class BGBConnection:
    def __init__(self):
        self.state = "handshake1"
        self.sock = None
        self.timestamp = 0

        self.send_buffer = []
        self.recv_buffer = []
        self.log_msgs = []
        self.msgs = []

        self.last_sent = 0


    def connect(self, host="localhost", port=8765):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket. TCP_NODELAY, 1)
        self.sock.connect((host, port))
        # self.sock.setblocking(False)


    async def loop(self):
        while True:
            await self.step()


    def run(self):
        asyncio.run(self.loop())


    def log(self, *msgs):
        line =', '.join(map(str, msgs))
        self.log_msgs.append(line)


    def recv_msg(self):
        try:
            data = self.sock.recv(8)
        except BlockingIOError as e:
            return None

        if data == b'':
            return None

        *reply, i1 = unpack("<BBBBI", data)
        msg = BGBMessage(*reply)

        if msg.cmd not in [bgb_cmd.sync3, bgb_cmd.joypad]:
            self.log('r', f"{self.state:9s}", msg)

        return msg


    def send(self, msg):
        self.timestamp += 1
        self.timestamp &= 0b_11111111_11111111_11111111_01111111

        data = pack("<BBBBI", msg.cmd, msg.b2, msg.b3, msg.b4, self.timestamp)
        if msg.cmd not in [bgb_cmd.sync3, bgb_cmd.joypad]:
            self.log('s', self.state, msg)
        cnt = self.sock.send(data)
        assert cnt == 8


    async def step(self):
        # print(f"{self.state=}, {self.send_buffer=}")

        if self.send_buffer and self.state == "connected":
            self.send(BGBMessage(bgb_cmd.sync1, self.send_buffer[0]))
            self.last_sent = perf_counter()
            self.state = "sending"
            await asyncio.sleep(0)

        msg = self.recv_msg()
        if msg == None:
            return

        if self.state == "handshake1":
            self.send(msg)
            self.state = "handshake2"
        elif self.state == "handshake2":
            if msg.cmd == bgb_cmd.sync2:
                self.send(msg)
                self.state = "connected"
            else:
                self.default_handler(sock, msg)
        elif self.state == "connected":
            if msg.cmd == bgb_cmd.sync1:
                if msg.b2 == 0:
                    line = bytearray(self.recv_buffer).decode('ascii')
                    self.msgs.append(line)
                    self.recv_buffer = []
                else:
                    self.recv_buffer.append(msg.b2)
                self.send(BGBMessage(bgb_cmd.sync2))
            else:
                self.default_handler(sock, msg)
        elif self.state == "sending":
            if msg.cmd == bgb_cmd.sync1:
                assert False, msg
            elif msg.cmd == bgb_cmd.sync2:
                if msg.b2 == 0x66:
                    self.state = "connected"
                    await asyncio.sleep(0.01)
                elif msg.b2 == 0x55:
                    self.send_buffer.pop(0)
                    self.state = "connected"
                else:
                    self.state = "connected"
                    # await asyncio.sleep(0.01)
                    await asyncio.sleep(0.1)
            else:
                self.default_handler(sock, msg)
        else:
            pass

        await asyncio.sleep(0)

        if self.state == "sending":
            elapsed = perf_counter() - self.last_sent
            if elapsed > 0.01:
                self.state = "connected"



    def default_handler(self, sock, msg):
        cmd = msg.cmd
        if cmd == bgb_cmd.status:
            self.send(msg)
        elif cmd == bgb_cmd.sync1:
            pass
        elif cmd == bgb_cmd.sync2:
            pass
        elif cmd == bgb_cmd.sync3:
            self.send(msg)
        elif cmd == bgb_cmd.joypad:
            pass
        else:
            pass


def link_gui(pipe, log_pipe):
    conn = BGBConnection()
    conn.connect()
    pipe.send("connected")
    asyncio.run(gui_loop(conn, pipe, log_pipe))


async def poll_pipe(conn, pipe):
    while pipe.poll():
        msg = pipe.recv()
        l = list(msg.encode('latin'))
        conn.send_buffer.extend(l)
    await asyncio.sleep(0)


async def gui_loop(conn, pipe, log_pipe):
    while True:
        await conn.step()

        await poll_pipe(conn, pipe)
        await poll_pipe(conn, log_pipe)

        while conn.msgs:
            pipe.send(conn.msgs.pop(0))

        while conn.log_msgs:
            log_pipe.send(conn.log_msgs.pop(0))



if __name__ == "__main__":
    conn = BGBConnection()
    conn.connect()
    conn.run()


