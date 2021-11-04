from tkinter import *
from tkinter.ttk import *

from ctypes import windll
from multiprocessing import Process, Pipe
from time import sleep


class MsgApp:
    def __init__(self, root):
        self.root = root

        root.title('GB Messages')
        root.geometry('500x400')

        pw = PanedWindow(orient=HORIZONTAL)

################################

        lhs = Frame(root)
        lhs.pack(side=LEFT)

        lhs_sub = Frame(lhs)
        lhs_sub.pack(side=TOP, expand=True, fill=BOTH)

        self.msgs = left_list = Listbox(lhs_sub)
        left_list.pack(side=LEFT, expand=True, fill=BOTH)

        left_scroll = Scrollbar(lhs_sub)
        left_scroll.pack(side=RIGHT, fill=BOTH)

        left_list.config(yscrollcommand=left_scroll.set)
        left_scroll.config(command=left_list.yview)

        self.input_text = StringVar()
        textbox = Entry(lhs, textvariable=self.input_text, font=('arial', 15, 'bold'))
        textbox.pack(side=BOTTOM, fill=X)
        textbox.focus()

        textbox.bind('<Return>', self.send_msg)

        pw.add(lhs)
################################

        rhs = Frame(root)
        rhs.pack(side=RIGHT)

        self.logs = right_list = Listbox(rhs)
        right_list.pack(side=LEFT, expand=True, fill=BOTH)

        right_scroll = Scrollbar(rhs)
        right_scroll.pack(side=RIGHT, fill=BOTH)

        right_list.config(yscrollcommand=right_scroll.set)
        right_scroll.config(command=right_list.yview)

        pw.add(rhs)

################################

        pw.pack(fill=BOTH, expand=True)

        self.main_pipe, child_main = Pipe()
        self.log_pipe,  child_log = Pipe()

        self.p = p = Process(target=link_client, args=(child_main, child_log))
        p.start()

        root.after(100, self.poll_client)


    def __enter__(self):
        print("enter?")


    def __exit__(self, exc_type, exc_value, traceback):
        print("exit?")


    def __del__(self):
        print("die?")
        self.p.terminate()


    def poll_client(self):
        while self.log_pipe.poll():
            line = self.log_pipe.recv()
            self.logs.insert(END, line)

        while self.main_pipe.poll():
            line = self.main_pipe.recv()
            self.msgs.insert(END, line)

        self.root.after(100, self.poll_client)


    def send_msg(self, e):
        print(f"msg {self.input_text.get()}")
        self.input_text.set("")


def link_client(main, log):
    while True:
        main.send("hi main")
        sleep(1)
        log.send("hi log")
        sleep(1)
        log.send("bye log")
        sleep(1)
        main.send("bye main")
        sleep(2)


def main():
    root = Tk()
    with MsgApp(root) as app:
        root.after(10_000, root.destroy)
        root.mainloop()


if __name__ == "__main__":
    main()

