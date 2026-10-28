"""Bounded TCP connect / UDP probes. No evasion or spoofing."""
import errno
import logging
import socket
import time
from .filter_utils import allowed_target, parse_ports

LOG = logging.getLogger('netrecon')


def scan_ports(target, ports, protocol='tcp', rate_limit=10, timeout=0.3,
               whitelist=('127.0.0.0/8',), blacklist=()):
    target = allowed_target(target, whitelist, blacklist)
    ports = parse_ports(','.join(map(str, ports)))
    if protocol not in ('tcp', 'udp') or not 1 <= rate_limit <= 100:
        raise ValueError('Protocol tcp/udp; rate limit 1-100 probes/second')
    if not 0.05 <= timeout <= 2:
        raise ValueError('Timeout must be 0.05-2 seconds')
    LOG.info('SCAN START target=%s protocol=%s ports=%s rate=%s', target, protocol, ports, rate_limit)
    result = []
    previous = None
    for port in ports:
        if previous is not None:
            time.sleep(max(0, 1/rate_limit - (time.monotonic() - previous)))
        previous = time.monotonic()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM if protocol == 'tcp' else socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            try:
                if protocol == 'tcp':
                    status = sock.connect_ex((target, port))
                    state = 'open' if status == 0 else 'closed' if status == errno.ECONNREFUSED or status == 10061 else 'filtered/unknown'
                else:
                    sock.connect((target, port))
                    sock.send(b'LAB03-PROBE')
                    sock.recv(1024)
                    state = 'open'
            except socket.timeout:
                state = 'open|filtered' if protocol == 'udp' else 'filtered/unknown'
            except ConnectionRefusedError:
                state = 'closed'
            except OSError:
                state = 'unknown'
        row = {'port': port, 'protocol': protocol, 'state': state}
        result.append(row)
        LOG.info('PROBE target=%s port=%s/%s state=%s', target, port, protocol, state)
    LOG.info('SCAN END target=%s probes=%s', target, len(result))
    return result


async def async_scan_ports(target, ports, rate_limit=10):
    import asyncio
    return await asyncio.to_thread(scan_ports, target, ports, rate_limit=rate_limit)
