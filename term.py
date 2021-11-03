# https://bgb.bircd.org/bgblink.html

from multiprocessing import Process, Pipe
from bgb_link import *

i = 0
def ere():
    global i
    i += 1
    print(i)


def print_messages(pipe, prefix=""):
    while pipe.poll():
        reply = pipe.recv()
        print(prefix, reply)


def main():
    main_pipe, child_main = Pipe()
    log_pipe,  child_log = Pipe()

    p = Process(target=link_client, args=(child_main, child_log))
    p.start()

    msg = main_pipe.recv()
    if msg != "connected":
        print(msg)
        exit(1)

    try:
        while True and p.is_alive():
            print_messages(main_pipe)
            print_messages(log_pipe, ">")

            line = input("# ")
            if line:
                main_pipe.send(line)

    except KeyboardInterrupt:
        p.terminate()

    print_messages(main_pipe)
    print_messages(log_pipe, ">")


if __name__ == '__main__':
    main()

