import argparse
import os
import socket
import ssl
import threading
from pathlib import Path
from message_encryption import MessageEncryption
from protocol import receive, send


class SecureChatClient:
    def __init__(self, username, key, room='lobby', certs='certs', port=8443, hostname='localhost', ca=None):
        certs = Path(certs)
        context = ssl.create_default_context(cafile=str(ca or certs/'ca/ca.crt'))
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(certs/f'client/{username}.crt', certs/f'client/{username}.key')
        raw = socket.create_connection(('127.0.0.1', port), timeout=3)
        try:
            self.sock = context.wrap_socket(raw, server_hostname=hostname)
        except Exception:
            raw.close()
            raise
        self.crypto = MessageEncryption(key)
        self.username, self.room = username, room
        send(self.sock, {'room': room})
        self.welcome = receive(self.sock)

    def send_message(self, text):
        if len(text.encode()) > 8192:
            raise ValueError('Maximum message: 8192 bytes')
        send(self.sock, {'type': 'message', 'ciphertext': self.crypto.encrypt(text, self.room, self.username)})

    def receive_message(self):
        packet = receive(self.sock)
        if packet['type'] == 'message':
            packet['text'] = self.crypto.decrypt(packet['ciphertext'], packet['room'], packet['sender'])
        return packet

    def join(self, room):
        send(self.sock, {'type': 'join', 'room': room})
        self.room = room

    def close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--user', choices=['alice', 'bob', 'carol'], default='alice')
    p.add_argument('--room', default='lobby')
    p.add_argument('--key', default='room.key')
    p.add_argument('--certs', default='certs')
    p.add_argument('--port', type=int, default=8443)
    p.add_argument('--generate-key', action='store_true')
    args = p.parse_args()
    if args.generate_key:
        with open(args.key, 'xb') as f:
            f.write(os.urandom(32))
        os.chmod(args.key, 0o600)
        print('Created client room key. Share privately with intended room members only.')
    else:
        client = SecureChatClient(args.user, Path(args.key).read_bytes(), args.room, args.certs, args.port)
        print(client.welcome)
        print('Type /join room to change room; /quit to exit.')
        def listen():
            try:
                while True:
                    print(client.receive_message())
            except (OSError, EOFError, ValueError):
                print('Disconnected')
        threading.Thread(target=listen, daemon=True).start()
        try:
            while True:
                text = input('> ')
                if text == '/quit':
                    break
                if text.startswith('/join '):
                    client.join(text[6:])
                else:
                    client.send_message(text)
        finally:
            client.close()
