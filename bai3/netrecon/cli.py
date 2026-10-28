import argparse
import json
import logging
from dotenv import load_dotenv
from engine import run_scan
from modules.filter_utils import parse_ports
from modules.email_sender import save_preview, send_email


def main():
    load_dotenv()
    p = argparse.ArgumentParser(description='Lab03 NetRecon: loopback lab scanner')
    p.add_argument('--target', default='127.0.0.1')
    p.add_argument('--ports', default='22,80,443')
    p.add_argument('--protocol', choices=['tcp', 'udp'], default='tcp')
    p.add_argument('--rate-limit', type=int, default=10, help='Maximum probes per second')
    p.add_argument('--mode', choices=['scan', 'service', 'banner', 'map', 'vuln', 'all'], default='all')
    p.add_argument('--nmap', action='store_true', help='Use installed Nmap -sT -sV on allowed target')
    p.add_argument('--email-preview', help='Save report as .eml without sending')
    p.add_argument('--send-email', help='Explicitly send to this recipient using SMTP environment variables')
    args = p.parse_args()
    logging.basicConfig(filename='netrecon.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        report = run_scan(args.target, parse_ports(args.ports), args.protocol, args.rate_limit, args.mode, args.nmap)
        body = json.dumps(report, ensure_ascii=False, indent=2)
        print(body)
        if args.email_preview:
            print('Email preview:', save_preview(args.email_preview, body))
        if args.send_email:
            send_email(args.send_email, 'Lab03 NetRecon', body)
            print('Email sent')
    except (ValueError, OSError) as exc:
        logging.warning('REJECTED %s', exc)
        p.error(str(exc))


if __name__ == '__main__':
    main()
