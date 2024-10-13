# import json
from aiokafka import AIOKafkaProducer
import requests # type: ignore
from fastapi import FastAPI, Depends, HTTPException,status
from sqlmodel import Session
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Annotated,List
from fastapi import FastAPI, Depends,HTTPException  # type: ignore

from sqlmodel import Session, select # type: ignore
import asyncio
import logging

from app.db import create_db_and_tables, get_session
from app.models import Inventory, InventoryCreate, InventoryUpdate
from app.inventory_crud.crud_inventory import create_inventory, update_inventory_item_by_id,validate_product_id, delete_inventory_by_id,get_inventory_list,get_inventory_by_id
from app.proto import inventory_pb2
from app import deps
from app.settings import KAFKA_INVENTORY_TOPIC,BOOTSTRAP_SERVER
from app.consumer.consumer_inventory import consume_messages

logging.basicConfig(level=logging.DEBUG)

# @asynccontextmanager
# async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    
#     logging.info("Lifespan event started...")
#     create_db_and_tables()
#     yield
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_db_and_tables()
    #consume msg
    task = asyncio.create_task(consume_messages(KAFKA_INVENTORY_TOPIC,BOOTSTRAP_SERVER))
    try:
        yield
    finally:
        task.cancel()
        await task


app = FastAPI(

              lifespan=lifespan,
              title=" Kafka With FastAPI",
              version="0.0.1",
              servers=[
        {
            "url": "http://127.0.0.1:8007", # ADD NGROK URL Here Before Creating GPT Action
            "description": "Development Server"
        }
        ])


@app.post("/inventories/", response_model=Inventory)
async def create_new_inventory(inventory: InventoryCreate,session: Annotated[Session, 
                               Depends(get_session)],producer: Annotated[AIOKafkaProducer, 
                               Depends(deps.get_kafka_producer)]) -> Inventory:
    # try:
        # product_id validation
        validate_product_id(inventory.product_id)
        
        # InventoryCreate  convert in toprototobuf Inventory 
        inventory_protobuf = inventory_pb2.Inventory(
            product_id=inventory.product_id,
            quantity=inventory.quantity,
            status_stock=inventory.status_stock
        )

        logging.info(f"Inventory Protobuf: {inventory_protobuf}")
        
        # Serialized data  into Protobuf 
        serialized_inventory = inventory_protobuf.SerializeToString()
        logging.info(f"Serialized Protobuf Data: {serialized_inventory}")

        # send to kafka
        await producer.send_and_wait(KAFKA_INVENTORY_TOPIC, serialized_inventory)
        logging.info(f"Kafka Product ID: {inventory.product_id} ")

        # CRUD 
        new_inventory = create_inventory(inventory, session)
        return new_inventory

    


# search by ID
@app.get("/inventory/{inventory_id}", response_model=Inventory)
def get_inventory_id(id: int, session: Session = Depends(get_session)):
    inventory = get_inventory_by_id(id,session)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return inventory

# list of all items
@app.get("/inventory/", response_model=List[Inventory])
def list_inventory_item(session:Annotated [Session , Depends(get_session)]):
    inventories = get_inventory_list(session)
    return inventories

@app.put("/products/{product_id}", response_model=Inventory)
async def update_product( product_id: int, inventory: InventoryUpdate,
                          session: Annotated[Session, Depends(get_session)],
                          producer: Annotated[AIOKafkaProducer,
                          Depends(deps.get_kafka_producer)] ) -> Inventory:
    
    # Update the inventory item in the database
    updated_inventory = update_inventory_item_by_id(product_id, inventory, session)
    
    if not updated_inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")

    # Create Inventory protobuf message
    inventory_protobuf = inventory_pb2.Inventory(
        # product_id=updated_inventory.product_id, 
        quantity=inventory.quantity,
        status_stock=inventory.status_stock 
    )

    logging.info(f"Inventory Protobuf for update: {inventory_protobuf}")

    # Create the InventoryOperation message with the operation
    product_message = inventory_pb2.InventoryOperation(
        operation_type=inventory_pb2.InventoryOperationType.UPDATE,
        inventory=inventory_protobuf  
    )

    # Serialize the message
    serialized_product_message = product_message.SerializeToString()

    logging.info(f"Serialized Inventory Message: {serialized_product_message}")

    # Produce the message to Kafka
    await producer.send_and_wait(KAFKA_INVENTORY_TOPIC, serialized_product_message)
    logging.info("Product update message sent to Kafka successfully.")

    return updated_inventory

@app.delete("/inventory/{inventory_id}")
def delete_inventory_id(id: int, session: Annotated[Session, Depends(get_session)]):
    deleted_inventory = delete_inventory_by_id(id, session)
    return deleted_inventory

#   get by prodcut id 
@app.get("/inventory/product/{product_id}", response_model=Inventory)
def get_inventory_by_product(product_id: int, session: Annotated[Session, Depends(get_session)]):
    # Validate the product ID using the session
    validate_product_id(product_id)
    
    # Now query the inventory using the session
    inventory = session.exec(select(Inventory).where(Inventory.product_id == product_id)).one_or_none()
    
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found for the provided product ID"
        )
    return inventory

    








# # increase item in inventory table
# @app.patch("/inventory/{product_id}/increase", response_model=Inventory)
# def increase_inventory_item(product_id: int, quntity_no: int, session:Annotated[ Session ,Depends(get_session)]):
#     inventory = increase_quantity(product_id, quntity_no, session)
#     if not inventory:
#         raise HTTPException(status_code=404, detail="Inventory not found")
#     return inventory

# # decrease quantity in db 
# @app.patch("/inventory/{product_id}/decrease", response_model=Inventory)
# def decrease_inventory_item(product_id: int, quntity_no: int, session:Annotated[ Session , Depends(get_session)]):
#     inventory = decrease_quantity(product_id, quntity_no, session)
#     if not inventory:
#         raise HTTPException(status_code=404, detail="Inventory not found or insufficient quantity")
#     return inventory
#update
# @app.put("/inventories/{product_id}", response_model=Inventory)
# async def update_inventory(product_id: int,inventory: InventoryUpdate,
#                           session: Annotated[Session, Depends(get_session)])-> Inventory:
#     # producer: Annotated[AIOKafkaProducer, Depends(deps.get_kafka_producer)] ) -> Product:
#     updated_inventory = update_inventory_item(product_id, inventory, session)  
#     if not updated_inventory:
#         raise HTTPException(status_code=404, detail="Inventory ID not found")

#     # Serialize and inventory message
#     product_protobuf = product_pb2.Product(
#         product_id=updated_inventory.product_id,
#         quantity=updated_inventory.quantity,
#         status_stock=updated_inventory.status_stock,
    
        
#     )

#     logging.info(f"Product Protobuf: {product_protobuf}")
#     serialized_product = product_protobuf.SerializeToString()
#     logging.info(f"Serialized data: {serialized_product}")

#     await producer.send_and_wait("products", serialized_product) 
#     return updated_inventory


# def fetch_product(product_id: int):
#     response = requests.get(f"http://product-service/api/products/{product_id}")
#     if response.status_code == 200:
#         return response.json()
#     else:
#         raise HTTPException(status_code=404, detail="Product not found")

# # Function to create an inventory record
# def create_inventory(session: Session, product_id: int, quantity: int, price: float) -> Inventory:
#     inventory = Inventory(product_id=product_id, quantity=quantity, price=price)
#     session.add(inventory)
#     session.commit()
#     session.refresh(inventory)
#     return inventory

# # Function to update an inventory record
# def update_inventory(session: Session, product_id: int, quantity: int, price: float) -> Optional[Inventory]:
#     item = session.exec(select(Inventory).where(Inventory.product_id == product_id)).one_or_none()
#     if item:
#         item.quantity = quantity
#         item.price = price
#         session.add(item)
#         session.commit()
#         session.refresh(item)
#         return item
#     return None

# # Function to delete an inventory record
# def delete_inventory(session: Session, product_id: int) -> bool:
#     item = session.exec(select(Inventory).where(Inventory.product_id == product_id)).one_or_none()
#     if item:
#         session.delete(item)
#         session.commit()
#         return True
#     return False

# # Testing route
# @app.get("/")
# def read_root():
#     return {"inventory": "Service"}

# @app.post("/inventory/")
# def add_inventory(product_id: int, quantity: int, price: float, session: Session = Depends(get_session)):
#     # Check if product exists
#     fetch_product(product_id)
    
#     # Create inventory record
#     return create_inventory(session, product_id, quantity, price)

# @app.get("/inventory/{product_id}")
# def get_inventory_endpoint(product_id: int, session: Session = Depends(get_session)):
#     inventory = session.exec(select(Inventory).where(Inventory.product_id == product_id)).one_or_none()
#     if not inventory:
#         raise HTTPException(status_code=404, detail="Inventory not found")
#     return inventory

# @app.get("/inventory/")
# def list_inventory_endpoint(session: Session = Depends(get_session)):
#     inventories = session.exec(select(Inventory)).all()
#     return inventories

# @app.put("/inventory/{product_id}")
# def update_inventory_endpoint(product_id: int, quantity: int, price: float, session: Session = Depends(get_session)):
#     inventory = update_inventory(session, product_id, quantity, price)
#     if not inventory:
#         raise HTTPException(status_code=404, detail="Inventory not found")
#     return inventory

# @app.delete("/inventory/{product_id}")
# def delete_inventory_endpoint(product_id: int, session: Session = Depends(get_session)):
#     success = delete_inventory(session, product_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Inventory not found")
#     return {"message": "Inventory deleted successfully"}


# def fetch_product(product_id: int):
#     response = requests.get(f"http://product-service/api/products/{product_id}")
#     if response.status_code == 200:
#         return response.json()
#     else:
#         raise HTTPException(status_code=404, detail="Product not found")

#  # testing route
# @app.get("/")
# def read_root():
#  return {"inventory": "Service"}
# @app.post("/inventory/")
# def add_inventory(product_id: int, quantity: int, price: float, session: Session = Depends(get_session)):
#     # Check if product exists
#     fetch_product(product_id)
    
#     # Create inventory record
#     return create_inventory(session, product_id, quantity, price)

# @app.get("/inventory/{product_id}")
# def get_inventory(product_id: int, session: Session = Depends(get_session)):
#     inventory = get_inventory(session, product_id)
#     if not inventory:
#         raise HTTPException(status_code=404, detail="Inventory not found")
#     return inventory

# @app.get("/inventory/")
# def list_inventory(session: Session = Depends(get_session)):
#     inventories = list_inventory(session)
#     return inventories

# @app.put("/inventory/{product_id}")
# def update_inventory_endpoint(product_id: int, quantity: int, price: float, session: Session = Depends(get_session)):
#     inventory = update_inventory(session, product_id, quantity, price)
#     if not inventory:
#         raise HTTPException(status_code=404, detail="Inventory not found")
#     return inventory

# @app.delete("/inventory/{product_id}")
# def delete_inventory_endpoint(product_id: int, session: Session = Depends(get_session)):
#     success = delete_inventory(session, product_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Inventory not found")
#     return {"message": "Inventory deleted successfully"}

# @app.get("/inventory/{product_id}", response_model=Inventory)
# def read_inventory(product_id: int, session: Session = Depends(get_session)):
#     item = get_inventory_item(product_id, session)
#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")
#     return item

# @app.get("/inventory", response_model=List[Inventory])
# def list_inventory(session: Session = Depends(get_session)):
#     return get_all_inventory_items(session)

# @app.post("/inventory/update", response_model=Inventory)
# def update_inventory(product_id: int, inventory_data: InventoryBase, session: Session = Depends(get_session)):
#     item = update_inventory_item(product_id, inventory_data, session)
#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")
#     return item

# @app.put("/inventory/{product_id}/increase", response_model=Inventory)
# def increase_inventory(product_id: int, amount: int, session: Session = Depends(get_session)):
#     item = increase_quantity(product_id, amount, session)
#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")
#     return item

# @app.put("/inventory/{product_id}/decrease", response_model=Inventory)
# def decrease_inventory(product_id: int, amount: int, session: Session = Depends(get_session)):
#     item = decrease_quantity(product_id, amount, session)
#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")
#     return item


# # # search by id
# # @app.get("/inventory/{product_id}", response_model=Inventory)
# # def read_inventory(product_id: int, session: Session = Depends(get_session)):
# #     item = get_inventory_item(product_id, session)
# #     if not item:
# #         raise HTTPException(status_code=404, detail="Item not found")
# #     return item
# # # list of inventory item 
# # @app.get("/inventory", response_model=List[Inventory])
# # def list_inventory(session: Session = Depends(get_session)):
# #     return get_all_inventory_items(session)

# # # create inventory stock
# # @app.post("/inventory/update", response_model=InventoryBase)
# # def update_inventory( inventory_data: InventoryBase, session: Session = Depends(get_session)):
# #     try:
# #        updated_new = update_inventory_item( inventory_data, session)
# #        return updated_new 
# #     except Exception as e:
# #         print(f"Error: {str(e)}")  # Print the exception
# #         raise HTTPException(status_code=400, detail=f"Error creating order: {str(e)}")

# # # update when increase stock 
# # @app.put("/inventory/{product_id}/increase", response_model=Inventory)
# # def increase_inventory(product_id: int, amount: int, session: Session = Depends(get_session)):
# #     item = increase_quantity(product_id, amount, session)
# #     if not item:
# #         raise HTTPException(status_code=404, detail="Item not found")
# #     return item

# # # update when decrese stock( item del)
# # @app.put("/inventory/{product_id}/decrease", response_model=Inventory)
# # def decrease_inventory(product_id: int, amount: int, session: Session = Depends(get_session)):
# #     item = decrease_quantity(product_id, amount, session)
# #     if not item:
# #         raise HTTPException(status_code=404, detail="Item not found")
# #     return item
