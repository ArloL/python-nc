# python-nc

A test to see if I can implement nc's proxy functionality with python

## Usage

```
$ printf "GET / HTTP/1.0\r\n\r\n" | \
    python nc.py socks4 "${PROXY_HOST}" "${PROXY_PORT}" www.example.com 80
```

The goal was to use this as a ProxyCommand for ssh but it does not work:

```
$ ssh -o ProxyCommand="python nc.py socks4 ${PROXY_HOST} ${PROXY_PORT} %h %p" user@host 'command'
Connection to UNKNOWN port 65535 timed out
```

The same happens with https://github.com/dzonerzy/Pync
