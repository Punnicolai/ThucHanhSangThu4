import unittest
from unittest.mock import patch
from securevalidator import *
from app import app

class ValidatorTests(unittest.TestCase):
    def test_email_valid(self):
        for s in ['user@example.com', 'bun.nguyen+lab@hutech.edu.vn']:
            with self.subTest(s=s): self.assertTrue(validate_email(s))
    def test_email_invalid(self):
        for s in ['', 'user@@example..com', "' OR 1=1--@x.com", 'a@x.com\r\nBcc:test@x.com', '..a@x.com', None]:
            with self.subTest(s=s): self.assertFalse(validate_email(s))
    def test_url_public_ip(self): self.assertTrue(validate_url('https://8.8.8.8/'))
    def test_url_public_dns(self):
        with patch('securevalidator.core.socket.getaddrinfo',return_value=[(2,1,6,'',('93.184.216.34',443))]):
            self.assertTrue(validate_url('https://example.com/'))
    def test_url_private_and_bad_schemes(self):
        for s in ['http://127.0.0.1','http://10.0.0.1','http://169.254.169.254','http://[::1]/','http://[::ffff:127.0.0.1]','file:///etc/passwd','ftp://example.com','https://user:pass@example.com','http://localhost','http://2130706433','http://8.8.8.8:8080','http://8.8.8.8\n',None]:
            with self.subTest(s=s): self.assertFalse(validate_url(s))
    def test_url_mixed_dns_rejected(self):
        with patch('securevalidator.core.socket.getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',443)),(2,1,6,'',('10.0.0.1',443))]):
            self.assertFalse(validate_url('https://example.com'))
    def test_url_dns_failure(self):
        with patch('securevalidator.core.socket.getaddrinfo',side_effect=OSError): self.assertFalse(validate_url('https://invalid.example'))
    def test_filename_valid(self):
        for s in ['report.pdf','lab_01.txt','my report.csv']: self.assertTrue(validate_filename(s))
    def test_filename_traversal(self):
        for s in ['../secret.txt','..\\secret.txt','/etc/passwd','C:\\a.txt','%2e%2e%2fetc','%252e%252e%252fetc','CON.txt','file.txt:stream','name.','',None]:
            with self.subTest(s=s): self.assertFalse(validate_filename(s))
    def test_sql_demo(self): self.assertEqual(sanitize_sql_input("' OR 1=1 --"),'1=1')
    def test_sql_not_query_boundary(self):
        import sqlite3
        db=sqlite3.connect(':memory:'); db.execute('CREATE TABLE users (name TEXT)'); db.execute('INSERT INTO users VALUES (?)',('alice',))
        self.assertEqual(db.execute('SELECT name FROM users WHERE name=?',("' OR 1=1 --",)).fetchall(),[])
        db.close()
    def test_html_escape(self): self.assertEqual(sanitize_html_input('<script>alert(1)</script>'),'&lt;script&gt;alert(1)&lt;/script&gt;')
    def test_html_quotes(self): self.assertEqual(sanitize_html_input('"\''),'&quot;&#x27;')
    def test_web_form(self):
        r=app.test_client().post('/',data={'email':'user@example.com','url':'http://127.0.0.1','filename':'../bad.txt','html':'<script>alert(1)</script>'})
        self.assertEqual(r.status_code,200); self.assertNotIn(b'<script>alert(1)</script>',r.data)
    def test_api_bad_type(self): self.assertEqual(app.test_client().post('/validate',json={'email':42}).status_code,400)
    def test_api_json(self): self.assertFalse(app.test_client().post('/validate',json={'url':'http://127.0.0.1'}).get_json()['url'])
    def test_headers(self): self.assertIn('Content-Security-Policy',app.test_client().get('/').headers)

if __name__=='__main__': unittest.main(verbosity=2)
