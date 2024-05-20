from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import secrets
from django.conf import settings
import markdown as md
import smtplib
import unicodedata

'''
    This file contain the functions responsible to send email verification tokens to users.
    The email is sent using the SMTP protocol, and the email content is written in markdown
    and rendered to HTML using the markdown library.

    This file will be removed in future releases if django's built-in email
    functions are adopted.
'''

def normalize(s):
    return str(unicodedata.normalize('NFKD', s).encode('ascii', 'ignore'))

def generate_secure_otp(length = 8):
    return ''.join(
        secrets.choice('0123456789') for _ in range(length)
    )

email_body_md = '''

Hello {name},

Thank you for registering with ES4C. Please verify your email by clicking the link below:

[Verify Email]({link})

Or by inserting the following token in the verification page:

{token}

'''

email_subject_text = 'ES4C Email Verification — {name}, please verify your email'

def send_email_verification_token(user):
    email_settings = settings.VERIFICATION_EMAIL_SETTINGS
    message = MIMEMultipart()
    message['From'] = email_settings['smtp_sender']
    message['To'] = user.email
    message['Subject'] = email_subject_text.format(name = user.first_name + ' ' + user.last_name)
    email_content = md.markdown(
        email_body_md.format(
            name = user.first_name + ' ' + user.last_name,
            link = 'https://' + settings.HOST_FQDN + '/verify-email/{token}'.format(token = user.verification_token),
            token = user.verification_token
        )
    )
    message.attach(
        MIMEText(email_content, 'html')
    )
    with smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port']) as server:
        server.starttls()
        server.login(email_settings['smtp_username'], email_settings['smtp_password'])
        server.send_message(message)
        server.quit()
