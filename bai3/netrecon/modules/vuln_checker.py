def check_vulns(ports, banners=None):
    """Configuration hints, not CVE detection based solely on a port number."""
    hints = {21: 'FTP may send credentials in plaintext; prefer SFTP/FTPS',
             23: 'Telnet uses plaintext; disable or replace with SSH',
             80: 'HTTP may lack TLS; verify HTTPS and redirects',
             22: 'Review SSH password login, versions and patch level',
             443: 'Check TLS certificate, protocol and configuration'}
    findings = [{'port': port, 'level': 'review', 'detail': hints[port], 'confirmed_vulnerability': False}
                for port in ports if port in hints]
    for port, banner in (banners or {}).items():
        if 'Server:' in banner:
            findings.append({'port': port, 'level': 'info', 'detail': 'Server header discloses software information', 'confirmed_vulnerability': False})
    return findings
