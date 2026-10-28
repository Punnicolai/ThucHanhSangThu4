"""Run real TLS clients, TCP/UDP services, scanner, Flask routes and email preview."""
import contextlib
import json
import logging
import os
import socket
import socketserver
import ssl
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'secure-chat'))
sys.path.insert(0, str(ROOT/'netrecon'))
from make_certs import generate
from server import SecureChatServer
from client import SecureChatClient
from message_encryption import MessageEncryption
from protocol import receive, send
from engine import run_scan
from modules.filter_utils import allowed_target, parse_ports
from modules.port_scanner import scan_ports
from modules.email_sender import save_preview, compose_email
from app import app
from cryptography.exceptions import InvalidTag


class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(1)
        try:
            data = self.request.recv(2048)
            if data:
                self.request.sendall(b'HTTP/1.0 200 OK\r\nServer: Lab03Demo/1.0\r\nContent-Length: 0\r\n\r\n')
        except OSError:
            pass


class UDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data, sock = self.request
        sock.sendto(b'LAB03-ECHO:' + data, self.client_address)


class ThreadTCP(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_services(tcp_port=0, udp_port=0):
    tcp = ThreadTCP(('127.0.0.1', tcp_port), TCPHandler)
    udp = socketserver.ThreadingUDPServer(('127.0.0.1', udp_port), UDPHandler)
    udp.daemon_threads = True
    for server in (tcp, udp):
        threading.Thread(target=server.serve_forever, daemon=True).start()
    return tcp, udp


def main():
    evidence = ROOT/'docs/evidence'
    evidence.mkdir(parents=True, exist_ok=True)
    results = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        results.append(name)
        print(f'PASS {len(results):02d} | {name}', flush=True)
    def rejected(name, callback, errors=(ValueError,)):
        try:
            callback()
        except errors as exc:
            print(f'  rejected: {type(exc).__name__}: {exc}', flush=True)
            check(name, True)
        else:
            raise AssertionError(name + ': unexpectedly accepted')
    print('=== SECURECHAT: REAL SOCKET + MUTUAL TLS + CLIENT ENCRYPTION ===', flush=True)
    with tempfile.TemporaryDirectory() as temp:
        certs = Path(temp)/'certs'
        generate(certs)
        check('CA and certificate files generated', (certs/'server/server.crt').exists())
        server = SecureChatServer(certs, port=0)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        clients = []
        try:
            key = os.urandom(32)
            alice = SecureChatClient('alice', key, certs=certs, port=server.port)
            clients.append(alice)
            bob = SecureChatClient('bob', key, certs=certs, port=server.port)
            clients.append(bob)
            carol = SecureChatClient('carol', os.urandom(32), room='other', certs=certs, port=server.port)
            clients.append(carol)
            print('Alice TLS session:', alice.welcome, flush=True)
            check('TLS 1.2+ and certificate identity', alice.welcome['tls'] in ('TLSv1.2', 'TLSv1.3') and alice.welcome['sender'] == 'alice')
            alice.send_message('Xin chao Bob, day la tin nhan bao mat!')
            message = bob.receive_message()
            print('Bob received:', message['text'], flush=True)
            check('Alice -> Bob decrypts across real TLS sockets', message['text'] == 'Xin chao Bob, day la tin nhan bao mat!')
            print('Relay sees ciphertext:', server.transcript[-1]['ciphertext'], flush=True)
            check('Relay transcript contains no plaintext or room key', 'text' not in server.transcript[-1] and not hasattr(server, 'crypto'))
            bob.send_message('Chao Alice! Da nhan duoc tin.')
            check('Bob -> Alice reply', alice.receive_message()['text'] == 'Chao Alice! Da nhan duoc tin.')
            carol.sock.settimeout(0.2)
            rejected('Other room receives no lobby message', carol.receive_message, (socket.timeout,))
            bob.join('other')
            check('Room switch acknowledged', bob.receive_message()['room'] == 'other')
            # Carol uses a different room key: the relay still forwards but authentication fails.
            bob.send_message('Wrong key must not decrypt')
            rejected('Wrong room key rejected by AES-GCM', carol.receive_message, (InvalidTag,))
            crypto = MessageEncryption(key)
            token = crypto.encrypt('test', 'room', 'alice')
            check('AES-GCM round trip', crypto.decrypt(token, 'room', 'alice') == 'test')
            rejected('Message replay rejected', lambda: crypto.decrypt(token, 'room', 'alice'))
            rejected('Altered authenticated room rejected', lambda: MessageEncryption(key).decrypt(token, 'bad', 'alice'), (InvalidTag,))
            import base64
            raw = bytearray(base64.b64decode(token)); raw[-1] ^= 1
            rejected('Modified ciphertext rejected', lambda: MessageEncryption(key).decrypt(base64.b64encode(raw).decode(), 'room', 'alice'), (InvalidTag,))
            rejected('Wrong hostname rejected', lambda: SecureChatClient('alice', key, certs=certs, port=server.port, hostname='wrong.example'), (ssl.SSLCertVerificationError,))
            other = Path(temp)/'untrusted'
            generate(other)
            rejected('Untrusted CA rejected', lambda: SecureChatClient('alice', key, certs=certs, port=server.port, ca=other/'ca/ca.crt'), (ssl.SSLCertVerificationError,))
            def missing_cert():
                context = ssl.create_default_context(cafile=str(certs/'ca/ca.crt'))
                with context.wrap_socket(socket.create_connection(('127.0.0.1', server.port), timeout=2), server_hostname='localhost') as sock:
                    send(sock, {'room': 'lobby'})
                    receive(sock)
            rejected('Client without certificate rejected', missing_cert, (ssl.SSLError, OSError, EOFError))
            check('Concurrent clients tracked', len(server.connections.clients) == 3)
        finally:
            for client in clients:
                client.close()
            time.sleep(0.1)
            server.stop()
            worker.join(timeout=2)
        check('Clients removed after disconnect', not server.connections.clients)
    print('\n=== NETRECON: REAL TCP/UDP LOOPBACK SERVICES ===', flush=True)
    tcp, udp = start_services()
    try:
        tcp_port, udp_port = tcp.server_address[1], udp.server_address[1]
        with socket.socket() as unused:
            unused.bind(('127.0.0.1', 0))
            closed_port = unused.getsockname()[1]
        logging.getLogger('netrecon').addHandler(logging.FileHandler(evidence/'netrecon-demo.log', mode='w', encoding='utf-8'))
        logging.getLogger('netrecon').setLevel(logging.INFO)
        report = run_scan('127.0.0.1', [tcp_port, closed_port], rate_limit=20)
        print(json.dumps(report, indent=2), flush=True)
        by_port = {r['port']: r['state'] for r in report['scan']}
        check('Real TCP service found open', by_port[tcp_port] == 'open')
        check('Unused TCP port is not reported open (closed or filtered)', by_port[closed_port] in ('closed', 'filtered/unknown'))
        check('HTTP banner read over socket', 'Lab03Demo/1.0' in report['banner'][tcp_port])
        check('Network map contains actual open endpoint', f'{tcp_port}/tcp' in report['map']['services'])
        check('Findings do not falsely confirm a CVE', all(not r['confirmed_vulnerability'] for r in report['vuln']))
        udp_result = scan_ports('127.0.0.1', [udp_port], protocol='udp')
        print('UDP echo probe:', udp_result, flush=True)
        check('UDP response confirms open', udp_result[0]['state'] == 'open')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as silent:
            silent.bind(('127.0.0.1', 0))
            ambiguous = scan_ports('127.0.0.1', [silent.getsockname()[1]], protocol='udp', timeout=0.1)
        check('UDP silence is open|filtered, not falsely closed', ambiguous[0]['state'] == 'open|filtered')
        check('Port range parser', parse_ports('80,81-83,80') == [80,81,82,83])
        for invalid in ('0', '65536', '80-1', '1-129', 'abc'):
            rejected('Invalid ports blocked: '+invalid, lambda value=invalid: parse_ports(value))
        rejected('Target outside whitelist blocked before network', lambda: allowed_target('192.0.2.1'))
        rejected('Blacklist overrides whitelist', lambda: allowed_target('127.0.0.1', blacklist=['127.0.0.1/32']))
        rejected('Hostname rejected to prevent DNS rebinding', lambda: allowed_target('localhost'))
        rejected('Zero rate rejected', lambda: scan_ports('127.0.0.1', [tcp_port], rate_limit=0))
        start = time.monotonic()
        scan_ports('127.0.0.1', [tcp_port, closed_port], rate_limit=5)
        check('Rate limit spaces probes by >= 0.2 seconds', time.monotonic()-start >= 0.19)
        body = json.dumps(report, indent=2)
        preview = Path(tempfile.gettempdir())/'lab03-report.eml'
        save_preview(preview, body)
        check('Email report composed as RFC822 .eml', b'Subject:' in preview.read_bytes())
        preview.unlink()
        rejected('Email header injection rejected', lambda: compose_email('a\nBcc: x', 'test', 'body'))
        web = app.test_client()
        check('Flask homepage HTTP 200', web.get('/').status_code == 200)
        response = web.post('/scan', data={'target':'127.0.0.1','ports':str(tcp_port),'mode':'all','rate':'10','protocol':'tcp'})
        check('Flask form performs actual scan and displays result', response.status_code == 200 and b'Lab03Demo/1.0' in response.data)
        check('Flask rejects forbidden target with HTTP 400', web.post('/scan', data={'target':'192.0.2.1','ports':'80'}).status_code == 400)
        check('Flask rejects malformed ports', web.post('/scan', data={'target':'127.0.0.1','ports':'oops'}).status_code == 400)
        mail = web.post('/email-preview', data={'report':body})
        check('Flask email download is RFC822', mail.status_code == 200 and mail.mimetype == 'message/rfc822')
        check('Security headers present', 'frame-ancestors' in response.headers['Content-Security-Policy'])
        (evidence/'netrecon-result.json').write_text(body, encoding='utf-8')
        check('Timestamped activity log written', (evidence/'netrecon-demo.log').stat().st_size > 0)
    finally:
        for service in (tcp, udp):
            service.shutdown()
            service.server_close()
    summary = {'passed':len(results), 'checks':results, 'scope':'real sockets on 127.0.0.1; no external scan; no external email sent'}
    (evidence/'verification.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(f'\nALL {len(results)} CHECKS PASSED. Real TLS/TCP/UDP + Flask; no external email sent.', flush=True)


if __name__ == '__main__':
    main()
