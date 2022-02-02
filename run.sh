#!/bin/sh

set -o errexit
set -o nounset
set -o xtrace

# nc.py socks5   72.195.114.169       4145 www.example.com 80

PROXY_HOST=72.195.114.169
PROXY_PORT=4145

printf "GET / HTTP/1.0\r\n\r\n" | python2 ./Pync/nc.py --socks-port="${PROXY_PORT}" --socks-host="${PROXY_HOST}" www.example.com 80
#printf "GET / HTTP/1.0\r\n\r\n" | python nc.py socks4 "${PROXY_HOST}" "${PROXY_PORT}" www.example.com 80
#printf "GET / HTTP/1.0\r\n\r\n" | nc www.example.com 80
#printf "GET / HTTP/1.0\r\n\r\n" | nc -x "${PROXY_HOST}:${PROXY_PORT}" www.example.com 80

ssh  -o ProxyCommand="python2 ./Pync/nc.py --socks-port=${PROXY_PORT} --socks-host=${PROXY_HOST} %h %p" ansible@35.198.191.227 'whoami'
#ssh  -o ProxyCommand="python nc.py socks4 '${PROXY_HOST}' '${PROXY_PORT}' %h %p" ansible@35.198.191.227 'whoami'
#ssh -o ProxyCommand="nc -x '${PROXY_HOST}:${PROXY_PORT}' %h %p" ansible@35.198.191.227 'whoami'
