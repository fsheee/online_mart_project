from email.message import EmailMessage
import aiosmtplib
from app.config import MAIL_HOST,MAIL_PORT,MAIL_USERNAME,MAIL_PASSWORD,SMTP_FROM_EMAIL


async def send_email(data: dict):
    message = EmailMessage()
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = data["to"]  # List of recipient emails
    message["Subject"] = data["subject"]
    message.set_content(data["body"])

    # Send email through Mailtrap SMTP
    await aiosmtplib.send(
        message,
        hostname=MAIL_HOST,
        port=MAIL_PORT,
        username=MAIL_USERNAME,
        password=MAIL_PASSWORD,
        use_tls=False
    )


