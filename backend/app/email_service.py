
import smtplib
from email.message import EmailMessage

from app.database import settings


def send_verification_email(to_email: str, code: str):
    message = EmailMessage()

    message["Subject"] = "Blink Communication - Email Verification"
    message["From"] = settings.EMAIL_ADDRESS
    message["To"] = to_email

    message.set_content(
        f"""
Hello,

Welcome to Blink Communication!

Your email verification code is: {code}

This code expires in 10 minutes.

If you did not create an account, please ignore this email.

Blink Communication Team
"""
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(
            settings.EMAIL_ADDRESS,
            settings.EMAIL_APP_PASSWORD
        )
        server.send_message(message)



def send_password_reset_email(to_email: str, code: str):
    message = EmailMessage()

    message["Subject"] = "Blink Communication - Password Reset"
    message["From"] = settings.EMAIL_ADDRESS
    message["To"] = to_email

    message.set_content(f"""
Hello,

We received a request to reset your Blink Communication password.

Your password reset code is:

{code}

This code expires in 10 minutes.

If you did not request a password reset, please ignore this email.

Best regards,
Blink Communication Team
""")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(
            settings.EMAIL_ADDRESS,
            settings.EMAIL_APP_PASSWORD
        )
        server.send_message(message)