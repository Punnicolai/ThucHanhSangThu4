"""Client-only AES-256-GCM encryption; the relay never receives the room key."""
import base64
import json
import os
import uuid
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class MessageEncryption:
    def __init__(self, key):
        if len(key) != 32:
            raise ValueError('Room key must contain 32 bytes')
        self.cipher = AESGCM(key)
        self.seen = set()

    def encrypt(self, plaintext, room, sender):
        nonce = os.urandom(12)
        payload = json.dumps({'id': uuid.uuid4().hex, 'text': plaintext}, ensure_ascii=False).encode()
        aad = f'{room}:{sender}'.encode()
        return base64.b64encode(nonce + self.cipher.encrypt(nonce, payload, aad)).decode()

    def decrypt(self, token, room, sender):
        raw = base64.b64decode(token, validate=True)
        payload = json.loads(self.cipher.decrypt(raw[:12], raw[12:], f'{room}:{sender}'.encode()))
        if payload['id'] in self.seen:
            raise ValueError('Replay rejected')
        if len(self.seen) >= 10000:
            raise ValueError('Session limit reached; reconnect')
        self.seen.add(payload['id'])
        return payload['text']
