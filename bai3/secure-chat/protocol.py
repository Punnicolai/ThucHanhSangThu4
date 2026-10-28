import json
import struct

MAX_FRAME = 65536


def read_exact(sock, size):
    parts = bytearray()
    while len(parts) < size:
        chunk = sock.recv(size - len(parts))
        if not chunk:
            raise EOFError('Connection closed')
        parts.extend(chunk)
    return bytes(parts)


def receive(sock):
    size = struct.unpack('!I', read_exact(sock, 4))[0]
    if not 0 < size <= MAX_FRAME:
        raise ValueError('Invalid frame length')
    data = json.loads(read_exact(sock, size))
    if not isinstance(data, dict):
        raise ValueError('Expected JSON object')
    return data


def send(sock, data):
    raw = json.dumps(data, ensure_ascii=False).encode()
    if len(raw) > MAX_FRAME:
        raise ValueError('Message too large')
    sock.sendall(struct.pack('!I', len(raw)) + raw)
