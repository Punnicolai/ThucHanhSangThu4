import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path


def compose_email(to, subject, body, sender='lab03@example.invalid'):
    if any('\n' in value or '\r' in value for value in (to, subject, sender)):
        raise ValueError('Invalid email header')
    message = EmailMessage()
    message['From'], message['To'], message['Subject'] = sender, to, subject
    message.set_content(body)
    return message


def save_preview(path, body):
    Path(path).write_bytes(compose_email('student@example.invalid', 'Lab03 NetRecon report', body).as_bytes())
    return str(path)


def send_email(to, subject, body):
    """Explicit CLI opt-in only; SMTP credentials stay in the environment."""
    user = os.environ['SMTP_USER']
    message = compose_email(to, subject, body, user)
    with smtplib.SMTP(os.getenv('SMTP_HOST', 'smtp.gmail.com'), int(os.getenv('SMTP_PORT', '587')), timeout=15) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()
        smtp.login(user, os.environ['SMTP_PASS'])
        smtp.send_message(message)
