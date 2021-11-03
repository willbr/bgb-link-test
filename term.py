# https://bgb.bircd.org/bgblink.html

from multiprocessing import Process, Pipe
from bgb_link import *

i = 0
def ere():
    global i
    i += 1
    print(i)


def main():
    parent_conn, child_conn = Pipe()
    p = Process(target=link_client, args=(child_conn,))
    p.start()

    msg = parent_conn.recv()
    if msg != "connected":
        print(msg)
        exit(1)

    try:
        while True and p.is_alive():
            line = input("# ")
            parent_conn.send(line)
    except KeyboardInterrupt:
        p.terminate()


if __name__ == '__main__':
    main()

