"""Start owned loopback fixtures and the real Flask UI for manual verification."""
from demo import start_services, app

if __name__ == '__main__':
    tcp, udp = start_services(8080, 9999)
    print('Owned HTTP banner: 127.0.0.1:8080; UDP echo: 127.0.0.1:9999', flush=True)
    try:
        app.run(host='127.0.0.1', port=5000, debug=False)
    finally:
        for service in (tcp, udp):
            service.shutdown()
            service.server_close()
