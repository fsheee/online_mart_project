import asyncio
import logging
from aiokafka import AIOKafkaConsumer 
from google.protobuf.json_format import MessageToDict  
from http.client import HTTPException
from app.proto import payment_pb2  
from app.crud.payment_crud import add_new_payment, delete_payment_by_id, update_order, delete_order_by_id, update_payment  
from app.db import get_session
from app.models import Order, OrderCreate, OrderUpdate, Payment, PaymentCreate, PaymentResponse, PaymentUpdate 
from app.settings import KAFKA_CONSUMER_GROUP_ID_FOR_PAYMENT

logging.basicConfig(level=logging.INFO)



async def consume_messages(topic, bootstrap_servers):
    while True:
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=KAFKA_CONSUMER_GROUP_ID_FOR_PAYMENT,
                auto_offset_reset='earliest'
            )

            await consumer.start()
            logging.info("Consumer started successfully.")

            try:
                async for message in consumer:
                    # Deserialize message using Protobuf
                    payment_message = payment_pb2.paymentMessage()
                    try:
                        payment_message.ParseFromString(message.value)
                    except Exception as e:
                        logging.error(f"Error parsing message: {e}")
                        continue

                    logging.info(f"Deserialized Order Message: {payment_message}")

                    # Check if order ID is present
                    if not payment_message.HasField('payment_id'):
                        logging.error("Error: 'payment_id' is missing in the message.")
                        continue

                    # Extract the order ID and data
                    payment_id = payment_message.payment_id
                    payment_data = (
                        MessageToDict(payment_message.payment_data)
                        if payment_message.HasField('payment_data')
                        else None
                    )
                    
                    async with get_session() as session:
                        if payment_message.message_type == payment_pb2.MessageType.CREATE_PAYMENT and payment_data:
                            try:
                                logging.info("Adding Payment to Database")
                                payment = Payment(
                                    user_id=payment_data["user_id"],
                                    order_id=payment_data["order_id"],
                                    amount=payment_data["amount"],
                                    payment_method=payment_data["payment_method"],
                                    status=payment_data["pendding"],
                                    currency=payment_data["currency"],
                                ) 
                                session.add(payment)
                                await session.commit()
                                await session.refresh(payment)
                                logging.info(f"Added Order: {payment}")
                            except Exception as e:
                                logging.error(f"Error adding payment: {e}")

                        elif payment_message == payment_pb2.MessageType.edit_payment and payment_data:
                            logging.info(f"Payment update: {payment_data}")

                            # Extract payment_id
                            payment_id = payment_data["id"]

                            # Create PaymentUpdate instance
                            payment_update = PaymentUpdate(
                                status=payment_data.get("status")  # Only status is being updated for this example
                            )

                            # Update the payment in the database
                            updated_payment = update_payment(payment_id, payment_update, session)
                            if updated_payment:
                                logging.info(f"Updated Payment with ID: {payment_id}")
                            else:
                                logging.error(f"Payment with ID: {payment_id} not found.")

                        elif payment_message == payment_pb2.MessageType.delete_payment and payment_data:
                            # Ensure payment_id is extracted from the payment_data
                            payment_id = payment_data["id"]

                            try:
                                # Attempt to delete the payment by ID
                                deleted_payment = delete_payment_by_id(payment_id, session)  # Use await if it's an async function
                                if deleted_payment:
                                    logging.info(f"Deleted Payment: {payment_id}")
                                else:
                                    logging.error(f"Payment with ID: {payment_id} not found for deletion.")
                            except HTTPException as http_exc:
                                logging.error(f"HTTP error while deleting payment with ID {payment_id}: {http_exc.detail}")
                            except Exception as e:
                                logging.error(f"An unexpected error occurred while deleting payment with ID {payment_id}: {e}")
            finally:
                await consumer.stop()

        except Exception as e:
            logging.error(f"Error starting consumer: {e}")
            logging.info("Retrying in 5 seconds...")
            await asyncio.sleep(5)  