import asyncio
import logging
from aiokafka import AIOKafkaConsumer  # type: ignore
from google.protobuf.json_format import MessageToDict  # type: ignore
from http.client import HTTPException
from app.proto import inventory_pb2  # Assuming inventory protobuf file
from app.inventory_crud.crud_inventory import create_inventory, delete_inventory_by_id, update_inventory_item_by_id   
from app.db import get_session
from app.models import  InventoryCreate, InventoryUpdate
from app.settings import KAFKA_CONSUMER_GROUP_ID_FOR_INVENTORY 

logging.basicConfig(level=logging.INFO)

async def consume_messages(topic, bootstrap_servers):
    while True:
        try:
            consumer = AIOKafkaConsumer(topic,
                bootstrap_servers=bootstrap_servers,
                group_id=KAFKA_CONSUMER_GROUP_ID_FOR_INVENTORY,  
                auto_offset_reset='earliest'
            )

            await consumer.start()
            logging.info("Inventory consumer started successfully.")

            try:
                async for message in consumer:
                    logging.info(f"Raw message Value: {message.value}")

                    inventory_message = inventory_pb2.InventoryOperation()  
                    try:
                        inventory_message.ParseFromString(message.value)
                    except Exception as e:
                        logging.error(f"Error parsing message: {e}")
                        continue

                    logging.info(f"Deserialized data: {inventory_message}")

                    message_type = inventory_message.operation_type
                    inventory_data = (
                        MessageToDict(inventory_message.inventory_data) 
                        if inventory_message.HasField('inventory_data') 
                        else None
                    )
                    # Check if 'product_id' exists and is set in the message
                    if inventory_message.HasField('product_id') and inventory_message.product_id:
                        product_id = inventory_message.product_id
                        logging.info(f"Product ID: {product_id}")
                    else:
                         product_id = None  
                
                    async with get_session() as session:
                        if message_type == inventory_pb2.InventoryOperationType.CREATE and inventory_data:
                            try:
                                logging.info("Adding Inventory to Database")
                                inventory = InventoryCreate(
                                    product_id=inventory_data["product_id"],
                                    quantity=inventory_data["quantity"],
                                    status_stock=inventory_data["status_stock"]
                                )
                                await create_inventory(inventory, session)
                                logging.info(f"Added Inventory: {inventory}")
                            except Exception as e:
                                logging.error(f"Error adding inventory: {e}")

                        elif message_type == inventory_pb2.InventoryOperationType.UPDATE and inventory_data:
                            try:
                                logging.info(f"Updating Inventory: {inventory_data}")

                                inventory_update = InventoryUpdate(
                                    quantity=inventory_data["quantity"],
                                    stock_status=inventory_data["stock_status"]
                                )

                                await update_inventory_item_by_id(product_id, inventory_update, session)
                                logging.info(f"Updated Inventory with Product ID: {product_id}")
                            except Exception as e:
                                logging.error(f"Error updating inventory with Product ID {product_id}: {e}")

                        elif message_type == inventory_pb2.InventoryOperationType.DELETE and product_id:
                            logging.info(f"Deleting Inventory with Product ID: {product_id}")

                            try:
                                await delete_inventory_by_id(product_id, session)
                                logging.info(f"Deleted Inventory for Product ID: {product_id}")
                            except HTTPException as http_exc:
                                logging.error(f"HTTP error while deleting inventory with Product ID {product_id}: {http_exc.detail}")
                            except Exception as e:
                                logging.error(f"Unexpected error while deleting inventory with Product ID {product_id}: {e}")

            finally:
                await consumer.stop()

        except Exception as e:
            logging.error(f"Error starting consumer: {e}")
            logging.info("Retrying in 5 seconds...")
            await asyncio.sleep(5)
