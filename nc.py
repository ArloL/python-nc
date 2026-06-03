#!/usr/bin/env python

import contextlib
import os
import select
import sys

import socks


def nc():
    if len(sys.argv) < 6:
        print(
            "Usage : python nc.py proxy_type proxy_host proxy_port target_host target_port",
            file=sys.stderr,
        )
        sys.exit(1)

    proxy_type = socks.SOCKS4 if sys.argv[1] == "socks4" else socks.SOCKS5
    proxy_host = sys.argv[2]
    proxy_port = int(sys.argv[3])
    target_host = sys.argv[4]
    target_port = int(sys.argv[5])

    s = socks.socksocket()
    s.settimeout(10)

    try:
        s.set_proxy(proxy_type=proxy_type, addr=proxy_host, port=proxy_port)
        s.connect((target_host, target_port))
    except Exception as e:
        print(f"Unable to connect: {e}", file=sys.stderr)
        sys.exit(1)

    s.settimeout(None)
    stdin_fd = sys.stdin.fileno()
    stdout_fd = sys.stdout.fileno()
    stdin_open = True

    while True:
        rlist = [s]
        if stdin_open:
            rlist.append(stdin_fd)
        read_sockets, _, _ = select.select(rlist, [], [])

        for sock in read_sockets:
            if sock is s:
                data = s.recv(4096)
                if not data:
                    return 0
                os.write(stdout_fd, data)
            else:
                data = os.read(stdin_fd, 4096)
                if not data:
                    stdin_open = False
                    with contextlib.suppress(OSError):
                        s.shutdown(socks.socket.SHUT_WR)
                    continue
                s.sendall(data)


if __name__ == "__main__":
    sys.exit(nc())
