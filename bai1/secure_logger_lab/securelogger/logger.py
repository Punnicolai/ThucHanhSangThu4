"""JSON logging with redaction, gzip rotation and HMAC sidecars (single process)."""
import gzip
import hashlib
import hmac
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

PRIVATE_FIELDS = {'password', 'token', 'apikey', 'api_key', 'secret', 'authorization', 'phone', 'cccd', 'ssn'}


def mask_pii(value):
    if isinstance(value, dict):
        return {str(k): '<redacted>' if str(k).lower() in PRIVATE_FIELDS else mask_pii(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [mask_pii(v) for v in value]
    if not isinstance(value, str):
        return value
    value = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '<email_masked>', value)
    value = re.sub(r'(?i)\b(token|api[_-]?key|password|secret)\s*[:=]\s*[\"\x27]?[^\s,;\"\x27]+', r'\1=<redacted>', value)
    return re.sub(r'(?<!\w)(?:\+84|0)\d{9,11}(?!\w)', '<phone_or_id_masked>', value)


def get_key(folder):
    value = os.environ.get('LOG_INTEGRITY_KEY')
    if value:
        if len(value) < 32:
            raise ValueError('LOG_INTEGRITY_KEY must have at least 32 characters')
        return value.encode()
    path = Path(folder) / '.integrity.key'
    if not path.exists():
        try:
            with path.open('xb') as stream:
                stream.write(os.urandom(32))
            path.chmod(0o600)
        except FileExistsError:
            pass
    return path.read_bytes()


def verify_log(path, key):
    path = Path(path)
    sig = Path(str(path) + '.sig')
    if not path.exists():
        return not sig.exists()
    if not sig.exists():
        return False
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rb') as stream:
        lines = stream.readlines()
    signatures = sig.read_text(encoding='ascii').splitlines()
    if len(lines) != len(signatures):
        return False
    previous = b''
    for line, expected in zip(lines, signatures):
        digest = hmac.new(key, previous + line, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(digest, expected):
            return False
        previous = digest.encode('ascii')
    return True


class SecureHandler(logging.Handler):
    def __init__(self, path, key, max_bytes=1024 * 1024, backups=2):
        super().__init__()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.key, self.max_bytes, self.backups = key, max_bytes, backups
        if not verify_log(self.path, self.key):
            raise ValueError('Log integrity check failed')

    def rotate(self):
        for i in range(self.backups, 0, -1):
            target = Path(f'{self.path}.{i}.gz')
            target_sig = Path(str(target) + '.sig')
            if i == self.backups:
                target.unlink(missing_ok=True)
                target_sig.unlink(missing_ok=True)
            else:
                if target.exists(): target.replace(Path(f'{self.path}.{i+1}.gz'))
                if target_sig.exists(): target_sig.replace(Path(f'{self.path}.{i+1}.gz.sig'))
        with self.path.open('rb') as src, gzip.open(f'{self.path}.1.gz', 'wb') as dst:
            dst.write(src.read())
        Path(str(self.path) + '.sig').replace(Path(f'{self.path}.1.gz.sig'))
        self.path.unlink()

    def emit(self, record):
        if not verify_log(self.path, self.key):
            raise ValueError('Log integrity check failed; refusing to append')
        event = {'timestamp': datetime.now(timezone.utc).isoformat(), 'level': record.levelname,
                 'message': mask_pii(record.getMessage())}
        if hasattr(record, 'data'): event['data'] = mask_pii(record.data)
        if hasattr(record, 'results'): event['results'] = mask_pii(record.results)
        line = (json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
        if self.path.exists() and self.path.stat().st_size and self.path.stat().st_size + len(line) > self.max_bytes:
            self.rotate()
        sig = Path(str(self.path) + '.sig')
        previous = sig.read_text(encoding='ascii').splitlines()[-1].encode('ascii') if sig.exists() and sig.stat().st_size else b''
        digest = hmac.new(self.key, previous + line, hashlib.sha256).hexdigest()
        with self.path.open('ab') as stream: stream.write(line)
        with sig.open('a', encoding='ascii') as stream: stream.write(digest + '\n')
        self.path.chmod(0o600)
        sig.chmod(0o600)


def get_secure_logger(path='logs/secure.log', key=None, max_bytes=1024*1024, backups=2):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.Logger('secure_logger', level=logging.DEBUG)
    logger.propagate = False
    logger.addHandler(SecureHandler(path, key or get_key(path.parent), max_bytes, backups))
    return logger
