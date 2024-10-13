import os
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel, EmailStr

# Load environment variables from the .env file
load_dotenv()

# SMTP Configuration from environment variables
MAIL_HOST = os.environ.get("MAIL_HOST")  # Mailtrap SMTP server
MAIL_PORT = os.environ.get("MAIL_PORT")  # Mailtrap SMTP port
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")  # Mailtrap username
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")  # Mailtrap password
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL")  # Added SMTP_FROM_EMAIL

class MailBody(BaseModel):
    to: List[EmailStr]  # Validates email addresses
    subject: str
    body: str

