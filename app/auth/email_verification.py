import smtplib
from email.mime.text import MIMEText
from ..config import settings

async def send_verification_email(email: str, token: str):
    verification_link = f"https://linkconnect.vercel.app/verify-email?token={token}"
    message = MIMEText(f"Click to verify your account:\n{verification_link}")
    message["Subject"] = "Verify your email"
    message["From"] = settings.EMAIL_USER
    message["To"] = email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
        server.send_message(message)


async def send_reset_otp(email: str, token: str):
    otp = f"{token}"
    message = MIMEText(f"Your one time otp to reset your password:\n{otp}")
    message["Subject"] = "Reset your password"
    message["From"] = settings.EMAIL_USER
    message["To"] = email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
        server.send_message(message)
