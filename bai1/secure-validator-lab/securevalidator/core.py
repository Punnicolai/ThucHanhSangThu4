"""Input validation for lab 01. SQL filtering is a demonstration, not a query boundary."""
import html
import ipaddress
import re
import socket
from urllib.parse import urlsplit, unquote


def validate_email(email):
    if not isinstance(email, str) or len(email) > 254 or any(c in email for c in '\r\n\x00'):
        return False
    return re.fullmatch(r'[A-Za-z0-9_+.-]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+', email) is not None and '..' not in email and not email.startswith('.') and '.@' not in email


def validate_url(url):
    """Reject non-public targets. Does not fetch URLs or follow redirects."""
    if not isinstance(url, str) or len(url) > 2048 or any(ord(c) < 33 for c in url) or '\\' in url:
        return False
    try:
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in ('http', 'https') or not parsed.hostname or parsed.username is not None or parsed.password is not None:
            return False
        if parsed.port not in (None, 80, 443):
            return False
        host = parsed.hostname.lower().rstrip('.')
        if '%' in host or host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
            return False
        try:
            addresses = [ipaddress.ip_address(host)]
        except ValueError:
            if '.' not in host or not re.fullmatch(r'[a-z0-9.-]+', host):
                return False
            addresses = [ipaddress.ip_address(a[4][0]) for a in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)]
        return bool(addresses) and all(a.is_global and not a.is_multicast and not (getattr(a, 'ipv4_mapped', None) and not a.ipv4_mapped.is_global) for a in addresses)
    except (ValueError, OSError, UnicodeError):
        return False


def validate_filename(filename):
    if not isinstance(filename, str) or not 1 <= len(filename) <= 255:
        return False
    decoded = filename
    for _ in range(3):
        decoded = unquote(decoded)
    if decoded != filename or filename in ('.', '..') or '..' in filename or filename.endswith((' ', '.')):
        return False
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_. -]*', filename):
        return False
    stem = filename.split('.')[0].upper()
    return stem not in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}


def sanitize_sql_input(input_str):
    """Slide-compatible demo only. Real SQL must use bound parameters."""
    value = re.sub(r"(--|;|'|\"|#|/\*|\*/)", '', str(input_str))
    return re.sub(r'\b(OR|AND|SELECT|INSERT|DELETE|UPDATE|DROP|UNION|WHERE)\b', '', value, flags=re.I).strip()


def sanitize_html_input(html_str):
    return html.escape(str(html_str), quote=True)
