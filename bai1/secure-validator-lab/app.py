import os
from flask import Flask, jsonify, render_template, request
from securevalidator import validate_email, validate_url, validate_filename, sanitize_sql_input, sanitize_html_input

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16384


def process(data):
    fields = ('email', 'url', 'filename', 'sql', 'html')
    if not isinstance(data, dict) or any(not isinstance(data.get(k, ''), str) for k in fields):
        raise ValueError('All fields must be strings')
    return {'email': validate_email(data.get('email', '')), 'url': validate_url(data.get('url', '')),
            'filename': validate_filename(data.get('filename', '')), 'sql': sanitize_sql_input(data.get('sql', '')),
            'html': sanitize_html_input(data.get('html', ''))}


@app.route('/', methods=['GET', 'POST'])
def index():
    values = request.form.to_dict() if request.method == 'POST' else {}
    results = process(values) if request.method == 'POST' else None
    return render_template('index.html', results=results, values=values)


@app.post('/validate')
def validate():
    try:
        return jsonify(process(request.get_json(silent=True)))
    except ValueError:
        return jsonify(error='Expected a JSON object with string fields'), 400


@app.get('/health')
def health():
    return jsonify(status='ok')


@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; form-action 'self'"
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '5000')), debug=False)
