from starlette.config import Config # type: ignore
from starlette.datastructures import Secret     # type: ignore

try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

DATABASE_URL = config("DATABASE_URL", cast=Secret)
TEST_DATABASE_URL = config("TEST_DATABASE_URL", cast=Secret)

# kafka topic name
# KAFKA_TOPIC = config("KAFKA_TOPIC", cast=str)
KAFKA_PRODUCT_TOPIC=config("KAFKA_PRODUCT_TOPIC", cast=str)
BOOTSTRAP_SERVER=config("BOOTSTRAP_SERVER", cast=str)
KAFKA_ORDER_TOPIC=config("KAFKA_ORDER_TOPIC", cast=str)
KAFKA_USER_TOPIC=config("KAFKA_USER_TOPIC", cast=str)
KAFKA_ORDER_CREATED_TOPIC=config("KAFKA_ORDER_CREATED_TOPIC", cast=str)
KAFKA_ORDER_DELETED_TOPIC=config("KAFKA_ORDER_DELETED_TOPIC", cast=str)
KAFKA_ORDER_UPDATED_TOPIC=config("KAFKA_ORDER_UPDATED_TOPIC", cast=str)
# kafka consumer group id for each microservice
KAFKA_CONSUMER_GROUP_ID_FOR_PRODUCT=config("KAFKA_CONSUMER_GROUP_ID_FOR_PRODUCT", cast=str)
KAFKA_CONSUMER_GROUP_ID_FOR_ORDER=config("KAFKA_CONSUMER_GROUP_ID_FOR_ORDER", cast=str)
KAFKA_CONSUMER_GROUP_ID_FOR_NOTIFICATION=config("KAFKA_CONSUMER_GROUP_ID_FOR_NOTIFICATION", cast=str)


# # SMPTP server configuration
# SMTP_FROM_EMAIL=config("SMTP_FROM_EMAIL", cast=str)
# SMTP_SERVER = config("SMTP_SERVER", cast=str)
# SMTP_PORT=config("SMTP_PORT", cast=int)
# SMTP_USERNAME=config("SMTP_USERNAME", cast=str)
# SMTP_PASSWORD=config("SMTP_PASSWORD", cast=str)


