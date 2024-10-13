from starlette.config import Config
from starlette.datastructures import Secret


try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

# Database Configuration
DATABASE_URL = config("DATABASE_URL", cast=Secret).__str__()
TEST_DATABASE_URL = config("TEST_DATABASE_URL", cast=Secret).__str__()

# # Payment Service Configuration
# STRIPE_API_KEY = config("STRIPE_API_KEY", cast=Secret).__str__()

# # # GoPayFast Configuration
# PAYFAST_MERCHANT_ID = config("PAYFAST_MERCHANT_ID", cast=str)
# PAYFAST_MERCHANT_KEY = config("PAYFAST_MERCHANT_KEY", cast=str)
# PAYFAST_PASSWORD = config("PAYFAST_PASSWORD", cast=str)
# PAYFAST_URL = config("PAYFAST_URL", cast=str)


# Kafka Configuration
KAFKA_BOOTSTRAP_SERVER = config("BOOTSTRAP_SERVER", cast=str)  
KAFKA_PAYMENT_TOPIC = config("KAFKA_PAYMENT_TOPIC", cast=str)
KAFKA_PAYMENT_CREATED_TOPIC=config("KAFKA_PAYMENT_CREATED_TOPIC", cast=str)
KAFKA_PAYMENT_UPDATED_TOPIC=config("KAFKA_PAYMENT_UPDATED_TOPIC", cast=str)
KAFKA_PAYMENT_DELETED_TOPIC=config("KAFKA_PAYMENT_DELETED_TOPIC", cast=str)

KAFKA_CONSUMER_GROUP_ID_FOR_PAYMENT = config("KAFKA_CONSUMER_GROUP_ID_FOR_PAYMENT", cast=str)
KAFKA_ORDER_TOPIC = config("KAFKA_ORDER_TOPIC", cast=str)
KAFKA_USER_TOPIC = config("KAFKA_USER_TOPIC", cast=str)
KAFKA_NOTIFICATION_TOPIC = config("KAFKA_NOTIFICATION_TOPIC", cast=str)






