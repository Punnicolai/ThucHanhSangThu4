import os
from flask import Flask, jsonify, request
from securevalidator import validate_email, validate_url, validate_filename, sanitize_sql_input, sanitize_html_input
from securelogger import get_secure_logger

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16384
secure_logger = get_secure_logger(os.environ.get('SECURE_LOG_PATH', 'logs/secure.log'))


@app.post('/validate')
def validate():
    data = request.get_json(silent=True)
    fields = ('email', 'url', 'filename', 'sql', 'html')
    if not isinstance(data, dict) or any(not isinstance(data.get(k, ''), str) for k in fields):
        secure_logger.warning('Rejected invalid request structure')
        return jsonify(error='Expected string fields in a JSON object'), 400
    results = {'email':validate_email(data.get('email','')), 'url':validate_url(data.get('url','')),
               'filename':validate_filename(data.get('filename','')), 'sql':sanitize_sql_input(data.get('sql','')),
               'html':sanitize_html_input(data.get('html',''))}
    secure_logger.info('Validation performed', extra={'data':data, 'results':results})
    return jsonify(results)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT','5001')), debug=False)
