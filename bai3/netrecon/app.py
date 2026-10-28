import json
import logging
from flask import Flask, render_template, request, Response
from engine import run_scan
from modules.filter_utils import parse_ports
from modules.email_sender import compose_email

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8192
logging.basicConfig(filename='netrecon.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


@app.get('/')
def index():
    return render_template('index.html')


@app.post('/scan')
def scan():
    try:
        report = run_scan(request.form.get('target', ''), parse_ports(request.form.get('ports', '')),
                          request.form.get('protocol', 'tcp'), int(request.form.get('rate', '10')),
                          request.form.get('mode', 'all'))
        return render_template('result.html', result=report, pretty=json.dumps(report, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        logging.warning('WEB REJECTED %s', exc)
        return render_template('index.html', error=str(exc)), 400


@app.post('/email-preview')
def email_preview():
    body = request.form.get('report', '')
    if len(body) > 7000:
        return 'Report too large', 400
    message = compose_email('student@example.invalid', 'Lab03 NetRecon report', body)
    return Response(message.as_bytes(), mimetype='message/rfc822', headers={'Content-Disposition': 'attachment; filename=netrecon-report.eml'})


@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; frame-ancestors 'none'"
    return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
