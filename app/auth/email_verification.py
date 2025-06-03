import smtplib
from email.mime.text import MIMEText
from ..config import settings

async def send_verification_email(email: str, token: str):
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    message = MIMEText(f"Click to verify your account: {verification_link}")
    message["Subject"] = "Verify your email"
    message["From"] = settings.EMAIL_USER
    message["To"] = email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
        server.send_message(message)
