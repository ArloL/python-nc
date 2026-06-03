"""Minimal SOCKS5 CONNECT-only server for testing nc.py."""

import asyncio
import contextlib
import socket
import struct
import sys


async def relay(reader, writer):
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionError, OSError):
        pass
    try:
        if writer.can_write_eof():
            writer.write_eof()
    except OSError:
        pass


async def handle(client_reader, client_writer):
    try:
        ver, nmethods = await client_reader.readexactly(2)
        await client_reader.readexactly(nmethods)
        if ver != 5:
            client_writer.close()
            return
        client_writer.write(b"\x05\x00")
        await client_writer.drain()

        hdr = await client_reader.readexactly(4)
        ver, cmd, _, atyp = hdr
        if cmd != 1:
            client_writer.write(b"\x05\x07\x00\x01" + b"\x00" * 6)
            await client_writer.drain()
            client_writer.close()
            return
        if atyp == 1:
            host = socket.inet_ntoa(await client_reader.readexactly(4))
        elif atyp == 3:
            (n,) = await client_reader.readexactly(1)
            host = (await client_reader.readexactly(n)).decode()
        elif atyp == 4:
            host = socket.inet_ntop(
                socket.AF_INET6, await client_reader.readexactly(16)
            )
        else:
            client_writer.close()
            return
        (port,) = struct.unpack("!H", await client_reader.readexactly(2))
        print(f"[socks5] CONNECT {host}:{port}", file=sys.stderr)

        try:
            target_reader, target_writer = await asyncio.open_connection(host, port)
        except OSError as e:
            print(f"[socks5] connect failed: {e}", file=sys.stderr)
            client_writer.write(b"\x05\x05\x00\x01" + b"\x00" * 6)
            await client_writer.drain()
            client_writer.close()
            return

        client_writer.write(b"\x05\x00\x00\x01" + b"\x00" * 4 + b"\x00\x00")
        await client_writer.drain()

        await asyncio.gather(
            relay(client_reader, target_writer),
            relay(target_reader, client_writer),
        )
    except (asyncio.IncompleteReadError, ConnectionError):
        pass
    finally:
        with contextlib.suppress(OSError):
            client_writer.close()


async def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 1080
    server = await asyncio.start_server(handle, "127.0.0.1", port)
    print(f"[socks5] listening on 127.0.0.1:{port}", file=sys.stderr)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
