import json
import logging
from aiokafka import AIOKafkaConsumer  # Kafka consumer library
from app.db import get_session 

from app.db import get_session  # Database session utility
from app.crud.user_crud import create_user, update_user, authenticate as delete_user
from app.settings import KAFKA_CONSUMER_GROUP_ID_FOR_USER

logging.basicConfig(level=logging.INFO)

async def consume_messages(topic, bootstrap_servers):
    # Create a Kafka consumer instance
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=KAFKA_CONSUMER_GROUP_ID_FOR_USER,
        auto_offset_reset='earliest'
    )
    
    await consumer.start()
    try:
        # Continuously listen for messages from the topic
        async for message in consumer:
            try:
                user_data = json.loads(message.value.decode())
                logging.info(f"Received message: {user_data}")

                # Use a database session to process the user data
                with next(get_session()) as db:
                    if user_data['action'] == 'create':
                        create_user(db, user_data['user'])
                        logging.info(f"User created: {user_data['user']}")
                    elif user_data['action'] == 'update':
                        update_user(db, user_data['user'])
                        logging.info(f"User updated: {user_data['user']}")
                    elif user_data['action'] == 'delete':
                        delete_user(db, user_data['user_id'])
                        logging.info(f"User deleted with ID: {user_data['user_id']}")
                    else:
                        logging.warning(f"Unknown action received: {user_data['action']}")
            except json.JSONDecodeError:
                logging.error(f"Failed to decode message: {message.value.decode()}")
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                
    finally:
        # Ensure the consumer stops when done
        await consumer.stop()



# from http.client import HTTPException
# import json
# from aiokafka import AIOKafkaConsumer  # type: ignore
# from google.protobuf.json_format import MessageToDict  # type: ignore
# from app.proto import user_pb2
# # from app.crud.prd_crud import add_new_product, update_product_by_id, delete_product_by_id  # type: ignore
# from app.db import get_session
# # from app.models import Product, ProductAdd, ProductUpdate
# # import asyncio
# import logging
# import time

# from app.settings import KAFKA_CONSUMER_GROUP_ID_FOR_USER
# from app.auth import create_user, update_user, authenticate as delete_user

# logging.basicConfig(level=logging.INFO)
# async def consume_messages(topic, bootstrap_servers):
#     # Create a consumer instance.
#     consumer = AIOKafkaConsumer(
#         topic,
#         bootstrap_servers=bootstrap_servers,
#         group_id=KAFKA_CONSUMER_GROUP_ID_FOR_USER,
#         auto_offset_reset='earliest'
#     )
#     await consumer.start()
#     try:
#         async for message in consumer:
#             user_data = json.loads(message.value.decode())
#             with next(get_session()) as db:
#                 if user_data['action'] == 'create':
#                     create_user(db, user_data['user'])
#                 elif user_data['action'] == 'update':
#                     update_user(db, user_data['user'])
#                 elif user_data['action'] == 'delete':
#                     delete_user(db, user_data['user_id'])
#     finally:
#         await consumer.stop()

# from http.client import HTTPException
# from aiokafka import AIOKafkaConsumer  # type: ignore
# from google.protobuf.json_format import MessageToDict  # type: ignore
# from app.proto import product_pb2
# from app.crud.prd_crud import add_new_product, update_product_by_id, delete_product_by_id  # type: ignore
# from app.db import get_session
# from app.models import Product, ProductAdd, ProductUpdate, ProductResponse
# import asyncio
# import logging
# import time

# logging.basicConfig(level=logging.INFO)

# async def consume_messages(topic, bootstrap_servers):
#     while True:
#         try:
#             consumer = AIOKafkaConsumer(
#                 topic,
#                 bootstrap_servers=bootstrap_servers,
#                 group_id="my-group",
#                 auto_offset_reset='earliest'
#             )

#             await consumer.start()
#             logging.info("Consumer started successfully.")
            
#             try:
#                 async for message in consumer:
#                     try:
#                         logging.info(f"\n\nConsumer Raw message Value: {message.value}")

#                         product_message = product_pb2.ProductMessage()
#                         product_message.ParseFromString(message.value)
#                         logging.info(f"\n\nConsumer Deserialized data: {product_message}")

#                         message_type = product_message.message_type
#                         product_data = MessageToDict(product_message.product_data) if product_message.HasField('product_data') else None
#                         product_id = product_message.product_id if product_message.HasField('product_id') else None

#                         async with get_session() as session:
#                             if message_type == product_pb2.MessageType.add_product and product_data:
#                                 logging.info("Adding Product to Database")
#                                 product = Product(
#                                     product_name=product_data["product_name"],
#                                     description=product_data["description"],
#                                     price=product_data["price"],
#                                     expiry=product_data.get("expiry", ""),
#                                     brand=product_data.get("brand", ""),
#                                     weight=product_data.get("weight", 0.0),
#                                     category=product_data["category"]
#                                 )
#                                 session.add(product)
#                                 await session.commit()
#                                 await session.refresh(product)
#                                 logging.info(f"Added Product: {product}")
                            
#                             elif message_type == product_pb2.MessageType.edit_product and product_data:
#                                 if product_id is None:
#                                     raise ValueError("Product ID is missing for update operation.")

#                                 product_update = ProductUpdate(
#                                     product_name=product_data.get("product_name"),
#                                     description=product_data.get("description"),
#                                     price=product_data.get("price"),
#                                     expiry=product_data.get("expiry"),
#                                     brand=product_data.get("brand"),
#                                     weight=product_data.get("weight"),
#                                     category=product_data.get("category")
#                                 )

#                                 logging.info(f"Product update: {product_update}")

#                                 updated_product = await update_product_by_id(product_id, product_update, session)
#                                 logging.info(f"Updated Product with ID: {product_id}")
                              
#                             elif message_type == product_pb2.MessageType.delete_product:
#                               if product_id is None:
#                                 logging.error("Delete operation failed: 'product_id' is missing in the message.")
#                             else:
#                                try:
#                                    result = delete_product_by_id(product_id, session)
#                                    logging.info(f"Deleted Product: {result}")
#                                except HTTPException as http_exc:
#                                    logging.error(f"HTTP error while deleting product with ID {product_id}: {http_exc.detail}")
#                                except Exception as e:
#                                   logging.error(f"An unexpected error occurred while deleting product with ID {product_id}: {e}")


#                     #         elif message_type == product_pb2.MessageType.delete_product and product_id is not None:
#                     #             deleted_product = await delete_product_by_id(product_id, session)
#                     #             logging.info(f"Deleted Product: {deleted_product}")
                            
#                     #         else:
#                     #             logging.error("Unknown operation or missing data in message")

#                     # except Exception as e:
#                     #     logging.error(f"Error processing message: {e}")

#         finally:
#             await consumer.stop()

# except Exception as e:
#     logging.error(f"Error starting consumer: {e}")
#     logging.info("Retrying in 5 seconds...")
#     await asyncio.sleep(5)  # Use asyncio.sleep for non-blocking sleep

# # Running the consumer in an event loop
# if __name__ == "__main__":
#     topic = "products"
#     bootstrap_servers = "broker:19092"  

#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(consume_messages(topic, bootstrap_servers))


# from aiokafka import AIOKafkaConsumer  # type: ignore
# from google.protobuf.json_format import MessageToDict  # type: ignore
# from app.proto import product_pb2
# from app.crud.prd_crud import add_new_product, update_product_by_id, delete_product_by_id, get_product_by_id  # type: ignore
# from app.db import get_session
# from app.models import Product,ProductAdd, ProductUpdate,ProductResponse
# import asyncio
# import logging
# import time

# logging.basicConfig(level=logging.INFO)

# async def consume_messages(topic, bootstrap_servers):
#     while True:
#         try:
#             # Create a consumer instance.
#             consumer = AIOKafkaConsumer(
#                 topic,
#                 bootstrap_servers=bootstrap_servers,
#                 group_id="my-group",
#                 auto_offset_reset='earliest'
#             )

#             # Start the consumer.
#             await consumer.start()
#             logging.info("Consumer started successfully.")
            
#             try:
#                 # Continuously listen for messages.
#                 async for message in consumer:
#                     try:
#                         logging.info(f"\n\nConsumer Raw message Value: {message.value}")

#                         # Parse the message
#                         product_message = product_pb2.ProductMessage()
#                         product_message.ParseFromString(message.value)
#                         logging.info(f"\n\nConsumer Deserialized data: {product_message}")

#                         message_type = product_message.message_type
#                         product_data = MessageToDict(product_message.product_data) if product_message.HasField('product_data') else None
#                         product_id = product_message.product_id if product_message.HasField('product_id') else None
                  
                    

#                         async with get_session() as session:
#                             if message_type == product_pb2.MessageType.add_product and product_data:
#                                 logging.info("Adding Product to Database")
#                                 product = ProductAdd(
#                                     product_name=product_data["product_name"],
#                                     description=product_data["description"],
#                                     price=product_data["price"],
#                                     expiry=product_data.get("expiry", ""),
#                                     brand=product_data.get("brand", ""),
#                                     weight=product_data.get("weight", 0.0),
#                                     category=product_data["category"]
#                                 )
#                                 session.add(product)
#                                 await session.commit()
#                                 await session.refresh(product)
#                                 logging.info("Added Product:", product)
                            
#                             elif message_type == product_pb2.MessageType.edit_product and product_data:
                            
#                               product_update = ProductUpdate(
#                                 product_id=product_data.product_id,
#                                 product_name=product_data.product_name,
#                                 description=product_data.description,
#                                 price=product_data.price,
#                                 expiry=product_data.expiry,
#                                 brand=product_data.brand,
#                                 weight=product_data.weight,
#                                 category=product_data.category
#                               ) 
                            
#                               logging.info(f" product update: {product_update}")
        
#                             #   async with Session(engine) as session:
#                             #       update_product_db = await update_product_by_id(product_update.product_id, product_update, session)
#                               await update_product_by_id(product_update.product_id, product_update, session)
#                               logging.info(f"Updated Product with ID: {product_update.product_id}")
        
#                             elif message_type == product_pb2.MessageType.delete_product and product_id is not None:
#                                 delete_product_db = await delete_product_by_id(product_id, session)
#                                 logging.info("Deleted Product:", delete_product_db)
                            
                                
#                             else:
#                                 print("Unknown operation or missing data in message:", message_type)

#                     except Exception as e:
#                         print(f"Error processing message: {e}")

#             finally:
#                 # Ensure to close the consumer when done.
#                 await consumer.stop()

#         except Exception as e:
#             logging.error(f"Error starting consumer: {e}")
#             logging.info("Retrying in 5 seconds...")
#             time.sleep(5)

# # Running the consumer in an event loop
# if __name__ == "__main__":
#     topic = "products"
#     bootstrap_servers = "broker:19092"  

#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(consume_messages(topic, bootstrap_servers))
