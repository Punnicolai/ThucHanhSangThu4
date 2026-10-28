import argparse
import base64
import logging
import socket
import ssl
import threading
from pathlib import Path
from connection_manager import ConnectionManager
from room_manager import RoomManager
from protocol import receive, send

LOG = logging.getLogger('securechat')


class SecureChatServer:
    def __init__(self, certs='certs', host='127.0.0.1', port=8443):
        certs = Path(certs)
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.context.load_cert_chain(certs/'server/server.crt', certs/'server/server.key')
        self.context.load_verify_locations(certs/'ca/ca.crt')
        self.context.verify_mode = ssl.CERT_REQUIRED
        self.connections = ConnectionManager()
        self.rooms = RoomManager()
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((host, port))
        self.listener.listen(16)
        self.listener.settimeout(0.2)
        self.port = self.listener.getsockname()[1]
        self.stopped = threading.Event()
        self.transcript = []  # Contains ciphertext only, useful for the reproducible demo.

    def serve_forever(self):
        LOG.info('Listening on 127.0.0.1:%s; client certificate REQUIRED', self.port)
        while not self.stopped.is_set():
            try:
                raw, _ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self.handle, args=(raw,), daemon=True).start()

    def handle(self, raw):
        sock = None
        try:
            raw.settimeout(5)
            sock = self.context.wrap_socket(raw, server_side=True)
            username = dict(x[0] for x in sock.getpeercert()['subject'])['commonName']
            hello = receive(sock)
            room = hello.get('room')
            self.connections.add(sock, username)
            self.rooms.join(sock, room)
            send(sock, {'type': 'joined', 'sender': username, 'room': room, 'tls': sock.version()})
            LOG.info('Authenticated %s joined %s (%s)', username, room, sock.version())
            sock.settimeout(300)
            while True:
                message = receive(sock)
                if message.get('type') == 'join':
                    room = message.get('room')
                    self.rooms.join(sock, room)
                    self.connections.send_to(sock, {'type': 'joined', 'sender': username, 'room': room})
                elif message.get('type') == 'message':
                    token = message.get('ciphertext')
                    if not isinstance(token, str) or len(base64.b64decode(token, validate=True)) < 28:
                        raise ValueError('Invalid ciphertext')
                    packet = {'type': 'message', 'room': room, 'sender': username, 'ciphertext': token}
                    self.transcript.append(packet.copy())
                    self.transcript = self.transcript[-100:]
                    for peer in self.rooms.recipients(room, sock):
                        try:
                            self.connections.send_to(peer, packet)
                        except OSError:
                            self.rooms.leave(peer)
                else:
                    raise ValueError('Unknown command')
        except (ssl.SSLError, OSError, ValueError, EOFError, KeyError) as exc:
            LOG.info('Connection ended: %s', exc)
        finally:
            if sock:
                self.rooms.leave(sock)
                self.connections.remove(sock)
                sock.close()
            raw.close()

    def stop(self):
        self.stopped.set()
        self.listener.close()
        with self.connections.lock:
            clients = list(self.connections.clients)
        for client in clients:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            client.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--certs', default='certs')
    p.add_argument('--port', type=int, default=8443)
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    server = SecureChatServer(args.certs, port=args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()
