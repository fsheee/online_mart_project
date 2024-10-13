import asyncio
import logging
from aiokafka import AIOKafkaConsumer  # type: ignore
from google.protobuf.json_format import MessageToDict  # type: ignore
from http.client import HTTPException
from app.proto import product_pb2
from app.crud.prd_crud import add_new_product, update_product_by_id, delete_product_by_id  # type: ignore
from app.db import get_session
from app.models import Product, ProductAdd, ProductUpdate
from app.settings import  KAFKA_CONSUMER_GROUP_ID_FOR_PRODUCT

logging.basicConfig(level=logging.INFO)
async def consume_messages(topic, bootstrap_servers):
    while True:
        try:
            consumer = AIOKafkaConsumer(topic,
                bootstrap_servers=bootstrap_servers,
                group_id=KAFKA_CONSUMER_GROUP_ID_FOR_PRODUCT,
                auto_offset_reset='earliest'
                 
            )

            await consumer.start()
            logging.info("Consumer started successfully.")

            try:
                async for message in consumer:
                    logging.info(f"Consumer Raw message Value: {message.value}")

                    product_message = product_pb2.ProductMessage()
                    try:
                        product_message.ParseFromString(message.value)
                    except Exception as e:
                        logging.error(f"Error parsing message: {e}")
                        continue

                    logging.info(f"Consumer Deserialized data: {product_message}")

                    message_type = product_message.message_type

                    if not product_message.HasField('product_id'):
                        logging.error("Error: 'product_id' is missing in the message.")
                        continue

                    product_id = product_message.product_id

                    product_data = (
                        MessageToDict(product_message.product_data)
                        if product_message.HasField('product_data') 
                        else None
                    )

                    async with get_session() as session:
    #                     if product_message.message_type == product_pb2.MessageType.CREATE:
    # create_data = product_message.create
                        if message_type == product_pb2.OperationType.CREATE and product_data:
                            try:
                                logging.info("Adding Product to Database")
                                product = Product(
                                     product_id=None,  
                                    product_name=product_data["product_name"],
                                    description=product_data["description"],
                                    price=product_data["price"],
                                    expiry=product_data.get("expiry", ""),
                                    brand=product_data.get("brand", ""),
                                    # weight=product_data.get("weight", 0.0),
                                    category=product_data["category"]
                                )
                                session.add(product)
                                await session.commit()
                                await session.refresh(product)
                                logging.info(f"Added Product: {product}")
                            except Exception as e:
                                logging.error(f"Error adding product: {e}")

                        elif message_type == product_pb2.MessageType.UPDATE and product_data:
                            try:
                                logging.info(f"Updating Product: {product_data}")

                                product_update = ProductUpdate(
                                    product_id=product_id,
                                    product_name=product_data["product_name"],
                                    description=product_data["description"],
                                    price=product_data["price"],
                                    expiry=product_data.get("expiry", ""),
                                    brand=product_data.get("brand", ""),
                                    # weight=product_data.get("weight", 0.0),
                                    category=product_data["category"]
                                )

                                await update_product_by_id(product_id, product_update, session)
                                logging.info(f"Updated Product with ID: {product_id}")
                            except Exception as e:
                                logging.error(f"Error updating product with ID {product_id}: {e}")

                        elif message_type == product_pb2.MessageType.DELETE:
                            logging.info(f"Deleting Product with ID: {product_id}")

                            try:
                                await delete_product_by_id(product_id, session)
                                logging.info(f"Deleted Product: {product_id}")
                            except HTTPException as http_exc:
                                logging.error(f"HTTP error while deleting product with ID {product_id}: {http_exc.detail}")
                            except Exception as e:
                                logging.error(f"Unexpected error while deleting product with ID {product_id}: {e}")

            finally:
                await consumer.stop()

        except Exception as e:
            logging.error(f"Error starting consumer: {e}")
            logging.info("Retrying in 5 seconds...")
            await asyncio.sleep(5)

