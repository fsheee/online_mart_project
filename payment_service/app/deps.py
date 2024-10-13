from aiokafka import AIOKafkaProducer
import httpx # type: ignore

# Kafka Producer as a dependency
async def get_kafka_producer():
    producer = AIOKafkaProducer(bootstrap_servers='broker:19092')
    await producer.start()
    try:
        yield producer
    finally:
        await producer.stop()



# get httpx request from client
async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client
