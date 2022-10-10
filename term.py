from time import sleep, perf_counter
from bgb_link import *

class BGBConnection:
    def __init__(self, mode):
        self.mode = 'byte'

        self.state = None
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
        self.sock.setblocking(False)
        self.handshake()


    def recv_msg(self):
        try:
            data = self.sock.recv(8)
        except BlockingIOError as e:
            return None

        if data == b'':
            return None

        *reply, i1 = unpack("<BBBBI", data)
        msg = BGBMessage(*reply)

        return msg


    def send(self, msg):
        self.timestamp += 1
        self.timestamp &= 0b_11111111_11111111_11111111_01111111

        data = pack("<BBBBI", msg.cmd, msg.b2, msg.b3, msg.b4, self.timestamp)
        cnt = self.sock.send(data)
        assert cnt == 8


    def next_msg(self):
        msg = None
        while not msg:
            msg = self.recv_msg()
        return msg

    def handshake(self):
        msg = self.next_msg()
        assert msg.cmd == bgb_cmd.version
        self.send(msg)

        while True:
            msg = self.next_msg()
            cmd = msg.cmd

            if cmd == bgb_cmd.status:
                self.send(msg)
            elif cmd == bgb_cmd.sync1:
                print(f'sync1?: {msg}')
                assert False
            elif cmd == bgb_cmd.sync2:
                break
            elif cmd == bgb_cmd.sync3:
                self.send(msg)
            elif cmd == bgb_cmd.joypad:
                pass
            else:
                pass

        self.state = self.connected


    def recieve(self, msg):
        if self.mode == 'byte':
            self.msgs.append(msg.b2)
        elif self.mode == 'text':
            if msg.b2 == 0:
                line = bytearray(self.recv_buffer).decode('latin')
                self.msgs.append(line)
                self.recv_buffer = []
            else:
                self.recv_buffer.append(msg.b2)
        else:
            assert False
        self.send(BGBMessage(bgb_cmd.sync2))

    def connected(self, msg):
        if msg.cmd == bgb_cmd.sync1:
            self.recieve(msg)
        else:
            self.default_handler(sock, msg)

    def sending(self, msg):
        if msg.cmd == bgb_cmd.sync1:
            self.recieve(msg)
        elif msg.cmd == bgb_cmd.sync2:
            if msg.b2 == 0x66:
                self.state = self.connected
                sleep(0.01)
            elif msg.b2 == 0x55:
                self.send_buffer.pop(0)
                self.state = self.connected
            else:
                print(f'other b2 {msg.b2:02x}')
                self.send_buffer.pop(0)
                self.state = self.connected
                sleep(0.01)
        else:
            self.default_handler(sock, msg)

    def step2(self):
        msg = self.recv_msg()

        if msg:
            while msg:
                #print(msg)
                self.state(msg)
                msg = self.recv_msg()
        elif self.send_buffer:
            if self.state == self.connected:
                c = self.send_buffer[0]
                print(f'{c=}')
                self.send(BGBMessage(bgb_cmd.sync1, c))
                self.last_sent = perf_counter()
                self.state = self.sending
                sleep(0.01)
            elif self.state == self.sending:
                elapsed = perf_counter() - self.last_sent
                if elapsed > 0.04:
                    print('retry')
                    self.state = self.connected
            else:
                assert False
        else:
            print('no msg')

    def step(self):
        if self.send_buffer and self.state == self.connected:
            #print(f"{self.state=}, {self.send_buffer=}, {self.recv_buffer=}")
            self.send(BGBMessage(bgb_cmd.sync1, c))
            self.last_sent = perf_counter()
            self.state = self.sending
            sleep(0.01)

        msg = self.recv_msg()
        if msg == None:
            print('no msg')
            return

        self.state(msg)

        sleep(0.01)

        if self.state == self.sending:
            elapsed = perf_counter() - self.last_sent
            if elapsed > 0.01:
                print('retry')
                self.state = self.connected



    def default_handler(self, sock, msg):
        cmd = msg.cmd
        if cmd == bgb_cmd.status:
            self.send(msg)
        elif cmd == bgb_cmd.sync1:
            print(f'default sync1: {msg}')
            pass
        elif cmd == bgb_cmd.sync2:
            #print(f'default: {msg}')
            pass
        elif cmd == bgb_cmd.sync3:
            self.send(msg)
        elif cmd == bgb_cmd.joypad:
            pass
        else:
            pass


def main():
    conn = BGBConnection('text')
    conn.connect()

    conn.send_buffer.extend(b'\x01abcdefgh\n\x00')

    while conn.send_buffer:
        conn.step2()

if __name__ == '__main__':
    main()

