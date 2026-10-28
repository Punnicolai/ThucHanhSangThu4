import logging
from modules.port_scanner import scan_ports
from modules.banner_grabber import grab_banner
from modules.service_detector import detect_service
from modules.network_mapper import map_network
from modules.vuln_checker import check_vulns


def run_scan(target, ports, protocol='tcp', rate_limit=10, mode='all', nmap=False):
    if mode not in ('scan', 'service', 'banner', 'map', 'vuln', 'all'):
        raise ValueError('Unknown mode')
    rows = scan_ports(target, ports, protocol, rate_limit)
    open_ports = [row['port'] for row in rows if row['state'] == 'open']
    result = {'target': target, 'scan': rows}
    if protocol == 'tcp' and mode in ('all', 'banner', 'vuln'):
        result['banner'] = {p: grab_banner(target, p) for p in open_ports}
    if protocol == 'tcp' and mode in ('all', 'service'):
        result['service'] = detect_service(target, open_ports, nmap) if open_ports else {}
    if mode in ('all', 'map'):
        result['map'] = map_network(target, rows)
    if mode in ('all', 'vuln'):
        result['vuln'] = check_vulns(open_ports, result.get('banner'))
    logging.getLogger('netrecon').info('REPORT target=%s mode=%s result=%s', target, mode, result)
    return result
