import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_hi_email(to_email):
    sender_email = "scabca2020@gmail.com"
    sender_password = "lyae krue ufoz hryl"  # App Password (not your Gmail login password)

    subject = "Hello"
    body = "Hi"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    print("⏳ Attempting to send email...")  # Debug log

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        print(f"✅ Email sent successfully to {to_email}")
    except Exception as e:
        print("❌ Error sending email:", e)

# ✅ Force execution
if __name__ == "__main__":
    print("🚀 Script started.")  # Debug log
    send_hi_email("scadak2004@gmail.com")
