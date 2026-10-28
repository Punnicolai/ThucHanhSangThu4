import socket
from .filter_utils import allowed_target


def grab_banner(target, port, whitelist=('127.0.0.0/8',), blacklist=()):
    target = allowed_target(target, whitelist, blacklist)
    try:
        with socket.create_connection((target, int(port)), timeout=0.5) as conn:
            conn.sendall(b'HEAD / HTTP/1.0\r\nHost: localhost\r\n\r\n')
            return conn.recv(2048).decode('utf-8', errors='replace')
    except OSError as exc:
        return f'No banner: {type(exc).__name__}'
