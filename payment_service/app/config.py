
import os
from dotenv import load_dotenv

load_dotenv()

STRIPE_API_KnEY = os.environ.get("STRIPE_API_KEY")

# GoPayFast Configuration
PAYFAST_MERCHANT_ID = os.enviro.get("PAYFAST_MERCHANT_ID", cast=str)
PAYFAST_MERCHANT_KEY = os.environn.get("PAYFAST_MERCHANT_KEY", cast=str)

