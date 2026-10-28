from .filter_utils import allowed_target


def map_network(target, results):
    target = allowed_target(target)
    return {'host': target, 'reachable': any(r['state'] == 'open' for r in results),
            'services': [f"{r['port']}/{r['protocol']}" for r in results if r['state'] == 'open'],
            'scope': 'Only the explicitly selected host; no neighbor discovery'}
