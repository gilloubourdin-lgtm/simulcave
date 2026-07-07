# app/services/email.py

import os
import smtplib
from email.message import EmailMessage


def send_email(to_email: str, subject: str, body: str) -> bool:
    if os.getenv("EMAIL_BACKEND", "console") == "console":
        print("\n--- EMAIL DEV SimulCave ---")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(body)
        print("--- END EMAIL ---\n")
        return True

    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_FROM", "noreply@simulcave.ch")
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(
            os.getenv("SMTP_HOST"),
            int(os.getenv("SMTP_PORT", "587")),
            timeout=20,
        ) as smtp:
            smtp.starttls()
            smtp.login(
                os.getenv("SMTP_USER"),
                os.getenv("SMTP_PASSWORD"),
            )
            smtp.send_message(msg)

        print("Email envoyé à", to_email)
        return True

    except Exception as e:
        print("Erreur envoi email:", repr(e))
        print("TO:", to_email)
        print("SUBJECT:", subject)
        print(body)
        return False