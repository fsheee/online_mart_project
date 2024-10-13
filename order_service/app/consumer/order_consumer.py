import asyncio
import logging
from aiokafka import AIOKafkaConsumer 
from google.protobuf.json_format import MessageToDict  
from http.client import HTTPException
from app.proto import order_pb2  
from app.crud.order_crud import add_new_order, update_order, delete_order_by_id  
from app.db import get_session
from app.models import Order, OrderCreate, OrderUpdate 
from app.settings import KAFKA_CONSUMER_GROUP_ID_FOR_ORDER

logging.basicConfig(level=logging.INFO)



async def consume_messages(topic, bootstrap_servers):
    while True:
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=KAFKA_CONSUMER_GROUP_ID_FOR_ORDER,
                auto_offset_reset='earliest'
            )

            await consumer.start()
            logging.info("Consumer started successfully.")

            try:
                async for message in consumer:
                    # Deserialize message using Protobuf
                    order_message = order_pb2.OrderMessage()
                    try:
                        order_message.ParseFromString(message.value)
                    except Exception as e:
                        logging.error(f"Error parsing message: {e}")
                        continue

                    logging.info(f"Deserialized Order Message: {order_message}")

                    # Check if order ID is present
                    if not order_message.HasField('order_id'):
                        logging.error("Error: 'order_id' is missing in the message.")
                        continue

                    # Extract the order ID and data
                    order_id = order_message.order_id
                    order_data = (
                        MessageToDict(order_message.order_data)
                        if order_message.HasField('order_data')
                        else None
                    )
                    
                    async with get_session() as session:
                        if order_message.action == order_pb2.MessageType.CREATE_ORDER and order_data:
                            try:
                                logging.info("Adding Order to Database")
                                order = Order(
                                    user_id=order_data["user_id"],
                                    product_id=order_data["product_id"],
                                    product_name=order_data["product_name"],
                                    quantity=order_data["quantity"],
                                    shipping_address=order_data["shipping_address"],
                                    total_price=order_data["total_price"],
                                )
                                session.add(order)
                                await session.commit()
                                await session.refresh(order)
                                logging.info(f"Added Order: {order}")
                            except Exception as e:
                                logging.error(f"Error adding order: {e}")

                        elif order_message.action == order_pb2.MessageType.UPDATE_ORDER and order_data:
                            try:
                                logging.info(f"Updating Order: {order_data}")

                                order_update = OrderUpdate(
                                    # product_name=order_data.get("product_name"),
                                    quantity=order_data.get("quantity"),
                                    shipping_address=order_data.get("shipping_address"),
                                    total_price=order_data.get("total_price"),
                                )

                                await update_order(id, order_update, session)
                                logging.info(f"Updated Order with ID: {order_id}")
                            except Exception as e:
                                logging.error(f"Error updating order with ID {order_id}: {e}")

                        elif order_message.action == order_pb2.MessageType.DELETE_ORDER:
                            logging.info(f"Deleting Order with ID: {order_id}")

                            try:
                                await delete_order_by_id(id, session)
                                logging.info(f"Deleted Order: {order_id}")
                            except HTTPException as http_exc:
                                logging.error(f"HTTP error while deleting order with ID {order_id}: {http_exc.detail}")
                            except Exception as e:
                                logging.error(f"Unexpected error while deleting order with ID {order_id}: {e}")

            

            finally:
                await consumer.stop()
                logging.info("Consumer stopped.")

        except Exception as e:
            logging.error(f"Error starting consumer: {e}")
            logging.info("Retrying in 5 seconds...")
            await asyncio.sleep(5)


