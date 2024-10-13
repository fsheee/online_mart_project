from aiokafka import AIOKafkaProducer
import httpx

from app.settings import BOOTSTRAP_SERVER 

# Kafka Producer as a dependency
async def get_kafka_producer():
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)
    await producer.start()
    try:
        yield producer
    finally:
        await producer.stop()

# get httpx request from client
async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client




