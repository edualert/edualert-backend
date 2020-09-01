import smtplib
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import get_connection, EmailMultiAlternatives


def send_mail(subject, bodies, from_email, bcc, cc=None, fail_silently=False, auth_user=None, auth_password=None, connection=None):
    # Adapted the django.core.mail.send_mail implementation to our needs.
    connection = connection or get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently,
    )

    mail = EmailMultiAlternatives(subject=subject, from_email=from_email, to=cc or [], bcc=bcc, connection=connection)
    for mime_type, body in bodies.items():
        mail.attach_alternative(str(body), mime_type)
    mail.attach(logo_data())

    try:
        return mail.send()
    except smtplib.SMTPDataError as e:
        print(e)
        return None


def send_mass_mail(datatuple, fail_silently=False, auth_user=None, auth_password=None, connection=None):
    # Adapted the django.core.mail.send_mass_mail implementation to our needs.
    # datatuple must consist of a list of tuples (subject, bodies, from_email, bcc, cc - optional).
    connection = connection or get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently,
    )

    messages = []
    for email_data in datatuple:
        subject, bodies, sender, bcc = email_data[:4]
        cc = email_data[4] if len(email_data) >= 5 else []

        mail = EmailMultiAlternatives(subject=subject, from_email=sender, to=cc, bcc=bcc, connection=connection)
        for mime_type, body in bodies.items():
            mail.attach_alternative(str(body), mime_type)
        mail.attach(logo_data())

        messages.append(mail)

    try:
        return connection.send_messages(messages)
    except smtplib.SMTPDataError as e:
        print(e)
        return None


def logo_data():
    with open(settings.BASE_PATH + 'edualert/notifications/templates/logo.png', 'rb') as f:
        logo_content = f.read()
    logo = MIMEImage(logo_content)
    logo.add_header('Content-ID', '<logo>')
    return logo
