"""End-to-end tests for nc.py against the bundled SOCKS5 test server."""

import contextlib
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).parent
NC = ROOT / "nc.py"
SOCKS_SERVER = ROOT / "test_socks5_server.py"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_listen(port: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(("127.0.0.1", port))
                return
            except OSError:
                time.sleep(0.05)
    raise RuntimeError(f"nothing listening on 127.0.0.1:{port} after {timeout}s")


class EchoServer:
    """Plain TCP echo server: echoes whatever a single client sends, then closes."""

    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.received = bytearray()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        try:
            conn, _ = self.sock.accept()
        except OSError:
            return
        with conn:
            while True:
                try:
                    data = conn.recv(4096)
                except OSError:
                    return
                if not data:
                    return
                self.received.extend(data)
                try:
                    conn.sendall(data)
                except OSError:
                    return

    def close(self) -> None:
        with contextlib.suppress(OSError):
            self.sock.close()
        self._thread.join(timeout=2)


@pytest.fixture
def socks_proxy():
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, str(SOCKS_SERVER), str(port)],
        stderr=subprocess.PIPE,
    )
    try:
        _wait_for_listen(port)
        yield port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


@pytest.fixture
def echo_server():
    server = EchoServer()
    try:
        yield server
    finally:
        server.close()


def _run_nc(args: list[str], stdin: bytes, timeout: float = 10.0) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(NC), *args],
        input=stdin,
        capture_output=True,
        timeout=timeout,
    )


def test_usage_without_args():
    result = _run_nc([], stdin=b"")
    assert result.returncode == 1
    assert b"Usage" in result.stderr


def test_usage_with_too_few_args():
    result = _run_nc(["socks5", "127.0.0.1", "1080", "host"], stdin=b"")
    assert result.returncode == 1
    assert b"Usage" in result.stderr


def test_connect_failure_unreachable_proxy():
    # Pick a port nothing is listening on.
    dead_port = _free_port()
    result = _run_nc(
        ["socks5", "127.0.0.1", str(dead_port), "example.com", "80"],
        stdin=b"",
        timeout=15,
    )
    assert result.returncode == 1
    assert b"Unable to connect" in result.stderr


def test_socks5_echo_roundtrip(socks_proxy, echo_server):
    payload = b"hello over socks5\n"
    result = _run_nc(
        [
            "socks5",
            "127.0.0.1",
            str(socks_proxy),
            "127.0.0.1",
            str(echo_server.port),
        ],
        stdin=payload,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == payload
    assert bytes(echo_server.received) == payload


def test_socks5_large_payload(socks_proxy, echo_server):
    payload = b"A" * (64 * 1024) + b"\n"
    result = _run_nc(
        [
            "socks5",
            "127.0.0.1",
            str(socks_proxy),
            "127.0.0.1",
            str(echo_server.port),
        ],
        stdin=payload,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == payload


def test_socks5_target_unreachable(socks_proxy):
    dead_port = _free_port()
    result = _run_nc(
        ["socks5", "127.0.0.1", str(socks_proxy), "127.0.0.1", str(dead_port)],
        stdin=b"",
        timeout=15,
    )
    assert result.returncode == 1
    assert b"Unable to connect" in result.stderr


def test_proxy_type_defaults_to_socks5_for_unknown(socks_proxy, echo_server):
    # The argv parsing treats anything != "socks4" as socks5.
    payload = b"unknown-type-falls-back\n"
    result = _run_nc(
        [
            "wat",
            "127.0.0.1",
            str(socks_proxy),
            "127.0.0.1",
            str(echo_server.port),
        ],
        stdin=payload,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == payload
