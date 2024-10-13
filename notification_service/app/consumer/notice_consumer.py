import asyncio
import logging
import aiohttp
from http.client import HTTPException
from aiokafka import AIOKafkaConsumer  # type: ignore
from google.protobuf.json_format import MessageToDict  # type: ignore
from app.settings import  KAFKA_CONSUMER_GROUP_ID_FOR_NOTIFICATION
from app.email import send_email  
from app.proto.notification_pb2 import NotificationMessage

logging.basicConfig(level=logging.INFO)

async def consume_order_events():
    consumer = AIOKafkaConsumer(
        'order_events',
        bootstrap_servers='broker:19092',  
        group_id=KAFKA_CONSUMER_GROUP_ID_FOR_NOTIFICATION,
        auto_offset_reset='earliest'
    )
    
    await consumer.start()
    logging.info("Consumer started successfully.")

    try:
        async for message in consumer:
            # Parse the message using Protobuf
            notification_message = NotificationMessage()
            notification_message.ParseFromString(message.value)

            # Process Order Update
            if notification_message.HasField('order_update'):
                order_update = notification_message.order_update
                order_id = order_update.order_id
                user_id = order_update.user_id
                order_status = order_update.order_status

                # Fetch user email from user_service
                user_email = await fetch_user_email(user_id)

                if user_email:  # Ensure user_email is valid before sending
                    # Prepare the email content
                    email_data = {
                        "to": [user_email],
                        "subject": f"Order Update: {order_id}",
                        "body": f"Hi,\n\nYour order with ID {order_id} is now {order_status}.\n\nThank you for shopping with us!"
                    }

                    # Send the email asynchronously
                    await asyncio.to_thread(send_email, email_data)  # Adjust if send_email is async
                    logging.info(f"Email sent for order ID: {order_id} to {user_email}")
                else:
                    logging.warning(f"No email found for user ID: {user_id}")

    except Exception as e:
        logging.error(f"Error while processing Kafka message: {e}")
    finally:
        await consumer.stop()

async def fetch_user_email(user_id: str) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://user_service/users/{user_id}') as response:
                response.raise_for_status()
                user_data = await response.json()
                return user_data.get('email')
    except Exception as e:
        logging.error(f"Failed to fetch user email: {e}")
        return None


