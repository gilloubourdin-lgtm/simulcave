import os
import smtplib
from email.message import EmailMessage


def send_email(to_email: str, subject: str, body: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not smtp_host or not smtp_user or not smtp_password:
        print("SMTP non configuré.")
        print("TO:", to_email)
        print("SUBJECT:", subject)
        print(body)
        return False

    msg = EmailMessage()
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    print("EMAIL_BACKEND =", os.getenv("EMAIL_BACKEND"))
    print("SMTP_HOST =", smtp_host)
    print("SMTP_PORT =", smtp_port)
    print("SMTP_USER =", smtp_user)
    print("SMTP_FROM =", smtp_from)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True

    except Exception as e:
        print("Erreur envoi email:", repr(e))
        print("TO:", to_email)
        print("SUBJECT:", subject)
        print(body)
        return False