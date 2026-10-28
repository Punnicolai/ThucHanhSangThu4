import re
import threading


class RoomManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.rooms = {}

    def join(self, sock, room):
        if not isinstance(room, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,32}', room):
            raise ValueError('Room: 1-32 letters, digits, _ or -')
        with self.lock:
            self.leave(sock)
            self.rooms.setdefault(room, set()).add(sock)

    def leave(self, sock):
        with self.lock:
            for room in list(self.rooms):
                self.rooms[room].discard(sock)
                if not self.rooms[room]:
                    del self.rooms[room]

    def recipients(self, room, sender):
        with self.lock:
            return list(self.rooms.get(room, set()) - {sender})
