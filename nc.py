#!/usr/bin/env python

import sys
import socket
import select
import socks

def nc():
    if(len(sys.argv) < 5) :
        print('Usage : python nc.py proxy_type proxy_host proxy_port target_host target_port')
        sys.exit()

    proxy_type = socks.SOCKS4 if sys.argv[1] == "socks4" else socks.SOCKS5
    proxy_host = sys.argv[2]
    proxy_port = int(sys.argv[3])
    target_host = sys.argv[4]
    target_port = int(sys.argv[5])

    s=socks.socksocket()
    s.settimeout(2)

    # connect to remote host
    try :
        s.set_proxy(
            proxy_type=proxy_type,
            addr=proxy_host,
            port=proxy_port
        )
        s.connect((target_host, target_port))
    except :
        print('Unable to connect')
        sys.exit()

    sys.stdout.flush()

    while 1:
        socket_list = [sys.stdin, s]

        # Get the list sockets which are readable
        read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])

        for sock in read_sockets:
            if sock == s:
                # incoming message from remote server
                data = sock.recv(4096)
                if not data :
                    print('\nDisconnected from chat server')
                    sys.exit()
                else :
                    #print data
                    sys.stdout.buffer.write(data)
                    sys.stdout.flush()

            else :
                # user entered a message
                msg = sys.stdin.buffer.read(1)
                s.send(msg)
                sys.stdout.flush()

if __name__ == "__main__":

    sys.exit(nc())
