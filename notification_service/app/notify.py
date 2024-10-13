import asyncio
from aiokafka import AIOKafkaConsumer
from email.message import EmailMessage
import aiosmtplib
from app.settings import (
    BOOTSTRAP_SERVER, 
    KAFKA_USER_TOPIC, 
    KAFKA_ORDER_CREATED_TOPIC, 
    KAFKA_ORDER_UPDATED_TOPIC, 
    KAFKA_CONSUMER_GROUP_ID_FOR_NOTIFICATION, 
    SMTP_SERVER, 
    SMTP_PORT, 
    SMTP_USERNAME, 
    SMTP_PASSWORD, 
    SMTP_FROM_EMAIL
)
from app.proto import notification_pb2  

async def send_email(to_email: str, subject: str, body: str):
    message = EmailMessage()
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    
    await aiosmtplib.send(
        message,
        hostname=SMTP_SERVER,
        port=SMTP_PORT,
        username=SMTP_USERNAME,
        password=SMTP_PASSWORD,
    )

async def consume_and_notify():
    consumer = AIOKafkaConsumer(
        KAFKA_USER_TOPIC, 
        KAFKA_ORDER_CREATED_TOPIC,
        KAFKA_ORDER_UPDATED_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVER,
        group_id=KAFKA_CONSUMER_GROUP_ID_FOR_NOTIFICATION
    )
    
    await consumer.start()
    try:
        async for message in consumer:
            notification_message = notification_pb2.NotificationMessage()
            notification_message.ParseFromString(message.value)  # Deserialize Protobuf message

            if notification_message.HasField("user_notification"):
                user_notification = notification_message.user_notification
                user_email = user_notification.email
                user_id = user_notification.id
            
            elif notification_message.HasField("order_notification"):
                order_notification = notification_message.order_notification
                order_id = order_notification.order_id
                order_status = order_notification.status
                user_id = order_notification.user_id

                # Email to the user
                if user_id and user_email:
                    subject = f"Order {order_id} - Status Update"
                    body = f"Your order with ID {order_id} is now {order_status}."
                    await send_email(user_email, subject, body)
    finally:
        await consumer.stop()

async def main():
    await consume_and_notify()

if __name__ == "__main__":
    asyncio.run(main())