from starlette.config import Config # type: ignore
from starlette.datastructures import Secret     # type: ignore

try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

DATABASE_URL = config("DATABASE_URL", cast=Secret)
BOOTSTRAP_SERVER = config("BOOTSTRAP_SERVER", cast=str)

KAFKA_PRODUCT_TOPIC = config("KAFKA_PRODUCT_TOPIC", cast=str)
# PRODUCT_SERVICE_URL = config("PRODUCT_SERVICE_URL", cast=str, default="http://localhost:8005")
PRODUCT_SERVICE_URL = config("PRODUCT_SERVICE_URL") 

# KAFKA_INVENTORY_TOPIC = config("KAFKA_INVENTORY_TOPIC", cast=str)

KAFKA_ORDER_TOPIC = config("KAFKA_ORDER_TOPIC", cast=str)

KAFKA_CONSUMER_GROUP_ID_FOR_PRODUCT = config("KAFKA_CONSUMER_GROUP_ID_FOR_PRODUCT", cast=str)
# KAFKA_CONSUMER_GROUP_ID_FOR_INVENTORY = config("KAFKA_CONSUMER_GROUP_ID_FOR_INVENTORY", cast=str)

TEST_DATABASE_URL = config("TEST_DATABASE_URL", cast=Secret)



