"""Generate a private lab CA, a SAN server certificate and per-user client certificates."""
import argparse
import datetime as dt
import ipaddress
import os
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID


def generate(root):
    root = Path(root)
    if root.exists() and any(root.iterdir()):
        raise ValueError('Certificate folder is not empty; refusing to overwrite keys')
    root.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    def key():
        return rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_key = key()
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Lab03 Private CA')])
    def builder(name, public_key):
        return (x509.CertificateBuilder().subject_name(name).issuer_name(ca_name)
                .public_key(public_key).serial_number(x509.random_serial_number())
                .not_valid_before(now - dt.timedelta(minutes=5)).not_valid_after(now + dt.timedelta(days=365)))
    ca = (builder(ca_name, ca_key.public_key())
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), critical=True)
          .sign(ca_key, hashes.SHA256()))
    def save(sub, name, private, cert):
        folder = root / sub
        folder.mkdir(exist_ok=True)
        path = folder / f'{name}.key'
        with path.open('xb') as f:
            f.write(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        os.chmod(path, 0o600)
        (folder / f'{name}.crt').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    save('ca', 'ca', ca_key, ca)
    for username in ('server', 'alice', 'bob', 'carol'):
        private = key()
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost' if username == 'server' else username)])
        cert = (builder(name, private.public_key())
                .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH if username == 'server' else ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False))
        if username == 'server':
            cert = cert.add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'), x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), critical=False)
        save('server' if username == 'server' else 'client', username, private, cert.sign(ca_key, hashes.SHA256()))
    print(f'Created CA + localhost SAN server + alice/bob/carol mTLS certificates: {root}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='certs')
    generate(parser.parse_args().out)
