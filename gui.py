from tkinter import *
from tkinter.ttk import *
from bgb_link import *
from atest import *

from ctypes import windll
from multiprocessing import Process, Pipe

POLL_FREQ = 100 # ms

class MsgApp:
    def __init__(self, root):
        self.root = root

        root.title('GB Messages')
        root.geometry('800x600')

        pw = PanedWindow(orient=HORIZONTAL)

################################

        lhs = Frame(root)
        lhs.pack(side=LEFT)

        lhs_sub = Frame(lhs)
        lhs_sub.pack(side=TOP, expand=True, fill=BOTH)

        self.msgs = left_list = Listbox(lhs_sub, font=('Consolas', 15, 'bold'))
        left_list.pack(side=LEFT, expand=True, fill=BOTH)

        left_scroll = Scrollbar(lhs_sub)
        left_scroll.pack(side=RIGHT, fill=BOTH)

        left_list.config(yscrollcommand=left_scroll.set)
        left_scroll.config(command=left_list.yview)

        self.input_text = StringVar()
        textbox = Entry(lhs, textvariable=self.input_text, font=('Consolas', 15, 'bold'))
        textbox.pack(side=BOTTOM, fill=X)
        textbox.focus()

        textbox.bind('<Return>', self.send_msg)

        self.state = StringVar()
        self.state.set('Bytes')
        r1 = Radiobutton(lhs, text="Text", variable=self.state, val="Text")
        r1.pack(ancho=W)
        r2 = Radiobutton(lhs, text="Bytes", variable=self.state, val="Bytes")
        r2.pack(ancho=W)


        pw.add(lhs)
################################

        rhs = Frame(root)
        rhs.pack(side=RIGHT)

        self.logs = right_list = Listbox(rhs, font=('Consolas', 15, 'bold'))
        right_list.pack(side=LEFT, expand=True, fill=BOTH)

        right_scroll = Scrollbar(rhs)
        right_scroll.pack(side=RIGHT, fill=BOTH)

        right_list.config(yscrollcommand=right_scroll.set)
        right_scroll.config(command=right_list.yview)

        pw.add(rhs)

################################

        pw.pack(fill=BOTH, expand=True)

        self.main_pipe, self.child_main = Pipe()
        self.log_pipe,  self.child_log = Pipe()

        self.connect()

        root.after(POLL_FREQ, self.poll_client)


    def connect(self):
        self.p = p = Process(target=link_gui, args=(self.child_main, self.child_log))
        p.start()

        msg = self.main_pipe.recv()
        self.logs.insert(END, msg)

        if msg != "connected":
            self.main_pipe.send("ok")


    def poll_client(self):
        self.root.after(POLL_FREQ, self.poll_client)

        if not self.p.is_alive():
            return

        while self.log_pipe.poll():
            line = self.log_pipe.recv()
            self.logs.insert(END, line)
            self.logs.yview(END)

        while self.main_pipe.poll():
            line = self.main_pipe.recv()
            self.msgs.insert(END, f"remote: {line}")
            self.msgs.yview(END)

        # self.root.after(POLL_FREQ, self.poll_client)


    def send_msg(self, e):
        msg = self.input_text.get()
        state = self.state.get()
        self.msgs.insert(END, f"local:  {msg}")
        self.msgs.yview(END)
        if state == 'Bytes':
            raw = bytearray(int(n, 16) for n in msg.split(' '))
            new_msg = raw.decode('latin')
            self.main_pipe.send(new_msg)
        else:
            self.main_pipe.send(msg + '\0')
        self.input_text.set("")


def main():
    root = Tk()
    app = MsgApp(root)
    # root.after(10_000, root.destroy)
    root.mainloop() 
    app.p.terminate()


if __name__ == "__main__":
    main()

