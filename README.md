# python-nc

A Python implementation of `nc`'s SOCKS proxy functionality, usable as an SSH `ProxyCommand`.

## Usage

```
$ printf "GET / HTTP/1.0\r\n\r\n" | \
    uv run python nc.py socks4 "${PROXY_HOST}" "${PROXY_PORT}" www.example.com 80
```

As an SSH `ProxyCommand`:

```
$ ssh -o ProxyCommand="uv run --directory /path/to/python-nc python nc.py socks5 ${PROXY_HOST} ${PROXY_PORT} %h %p" user@host
```

## Development

Dependencies are managed with [uv](https://docs.astral.sh/uv/):

```
$ uv sync
```

Lint and format with ruff:

```
$ uv run ruff check .
$ uv run ruff format .
```

A minimal SOCKS5 CONNECT server is included for local testing:

```
$ uv run python test_socks5_server.py 1080
```
