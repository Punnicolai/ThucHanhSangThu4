import shutil
import socket
import subprocess
from .filter_utils import allowed_target, parse_ports


def detect_service(target, ports, use_nmap=False):
    target = allowed_target(target)
    ports = parse_ports(','.join(map(str, ports)))
    if use_nmap:
        executable = shutil.which('nmap')
        if not executable:
            raise ValueError('Nmap is not installed; install from nmap.org first')
        # Explicit TCP connect, bounded target and ports, normal visible probes.
        return subprocess.run([executable, '-sT', '-sV', '--version-light', '-Pn',
                               '--max-rate', '10', '--host-timeout', '30s', '-p',
                               ','.join(map(str, ports)), target], capture_output=True,
                              text=True, timeout=35, check=True).stdout
    result = {}
    for port in ports:
        try:
            result[port] = socket.getservbyport(port, 'tcp') + ' (port hint, unverified)'
        except OSError:
            result[port] = 'unknown; inspect banner or use --nmap'
    return result
