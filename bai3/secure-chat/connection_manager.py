import threading


class ConnectionManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.clients = {}

    def add(self, sock, username):
        with self.lock:
            if username in [x['username'] for x in self.clients.values()]:
                raise ValueError('Username already connected')
            if len(self.clients) >= 32:
                raise ValueError('Server full')
            self.clients[sock] = {'username': username, 'send_lock': threading.Lock()}

    def remove(self, sock):
        with self.lock:
            self.clients.pop(sock, None)

    def send_to(self, sock, data):
        from protocol import send
        with self.lock:
            info = self.clients.get(sock)
        if info:
            with info['send_lock']:
                send(sock, data)
