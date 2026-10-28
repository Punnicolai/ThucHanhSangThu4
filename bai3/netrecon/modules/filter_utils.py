import ipaddress


def allowed_target(target, whitelist=('127.0.0.0/8',), blacklist=()):
    """Require literal IPv4 to avoid DNS rebinding. Blacklist takes precedence."""
    address = ipaddress.IPv4Address(target)
    if any(address in ipaddress.ip_network(net) for net in blacklist):
        raise ValueError('Target is blacklisted')
    if not any(address in ipaddress.ip_network(net) for net in whitelist):
        raise ValueError('Target is outside the whitelist')
    return str(address)


def parse_ports(value):
    ports = set()
    for part in value.split(','):
        values = part.strip().split('-')
        if len(values) == 1:
            start = end = int(values[0])
        elif len(values) == 2:
            start, end = map(int, values)
        else:
            raise ValueError('Invalid port range')
        if not 1 <= start <= end <= 65535 or end - start >= 128:
            raise ValueError('Ports must be 1-65535; maximum 128 ports')
        ports.update(range(start, end + 1))
    if not ports or len(ports) > 128:
        raise ValueError('Maximum 128 ports')
    return sorted(ports)
