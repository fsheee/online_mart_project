from contextlib import asynccontextmanager

from typing import AsyncGenerator, List, Annotated
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, Depends, HTTPException,status
from httpx import AsyncClient
import httpx
from sqlmodel import Session
import asyncio
import logging
from datetime import datetime
from app.db import get_session, create_db_and_tables
from app.models import Order, OrderCreate, OrderResponse, OrderUpdate
from app.crud.order_crud import delete_order_by_id, get_all_orders, get_order_by_id, get_order_by_user_id, update_order

from app.consumer.order_consumer import consume_messages
from app.deps import get_http_client, get_kafka_producer
from app.settings import BOOTSTRAP_SERVER, KAFKA_ORDER_CREATED_TOPIC, KAFKA_ORDER_DELETED_TOPIC,KAFKA_ORDER_TOPIC, KAFKA_ORDER_UPDATED_TOPIC
from app.proto import order_pb2

logging.basicConfig(level=logging.DEBUG)

        
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logging.info("Lifespan event started...")
    
    # Initialize the database and create tables
    create_db_and_tables()

    # Start Kafka consumer task
    task = asyncio.create_task(consume_messages(KAFKA_ORDER_TOPIC, BOOTSTRAP_SERVER))

    try:
        yield 
    finally:
        logging.info("Lifespan event ended...")
        # Cancel the consumer task on shutdown
        task.cancel()
        """ Await task completion"""
        await task  


app = FastAPI(
    lifespan=lifespan,
    title="Kafka With FastAPI",
    version="0.0.1",
    servers=[
        {
            "url": "http://127.0.0.1:8008",
            "description": "Development Server"
        }
    ]
)

@app.get("/")
def read_root():
    return {"Order": "Service"}

"""fetch user tabel,product table and inventory"""

async def verify_user_product_inventory(order_create: OrderCreate, client: AsyncClient):
    # Define headers for authentication 
    headers = {"Authorization": "Bearer ur access tocken"}
    
    # Verify if the user exists in user_service
    user_response = await client.get(f"http://user2_service:8000/users/{order_create.user_id}", headers=headers)
    logging.info(f"User Service Response: {user_response.status_code}, {user_response.text}")
    if user_response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not exist")

    # Fetch product details from product_service
    product_response = await client.get(f"http://product_service:8000/products/{order_create.product_id}")
    logging.info(f"Product Service Response: {product_response.status_code}, {product_response.text}")
    if product_response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product does not exist")

    product_data = product_response.json()
    
    # Verify product name case insensitively
    provided_product_name = order_create.product_name.strip().lower()
    actual_product_name = product_data['product_name'].strip().lower()
    if provided_product_name != actual_product_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided product name does not match the actual product name.")

    # Check inventory availability stock
    inventory_response = await client.get(f"http://inventory_service:8000/inventory/product/{order_create.product_id}")
    logging.info(f"Inventory Service Response: {inventory_response.status_code}, {inventory_response.text}")
    if inventory_response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inventory information could not be retrieved")

    inventory_data = inventory_response.json()
    available_quantity = inventory_data['quantity']

    # Check if the ordered quantity exceeds the available stock
    if order_create.quantity > available_quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ordered quantity ({order_create.quantity}) exceeds available stock ({available_quantity})")

    return product_data


# """" order creation endpoint Encapsulates the logic for verifying user, product, and inventory.
# Returns the product_data if all verifications pass successfully."""


# Endpoint to create a new order
@app.post("/add_order/", response_model=OrderResponse)
async def create_order(order_add: OrderCreate, session:Annotated[Session , Depends(get_session)],
                       producer:Annotated[AIOKafkaProducer , Depends(get_kafka_producer)],
                       client: AsyncClient = Depends(get_http_client)):
    
    try:
        #  Verify user, product, and inventory details
        product_data = await verify_user_product_inventory(order_add, client)

        #  Calculate total price based on product price and order quantity
        total_price = product_data['price'] * order_add.quantity

        #  Create a protobuf Order object
        order_protobuf = order_pb2.Order(
            user_id=order_add.user_id,
            product_id=order_add.product_id,
            product_name=order_add.product_name,
            quantity=order_add.quantity,
            shipping_address=order_add.shipping_address,
            status="pending",
            created_at=datetime.utcnow().isoformat(),  # Convert to ISO format
            updated_at=datetime.utcnow().isoformat()
        )

        #  Create an OrderMessage for Kafka
        order_message = order_pb2.OrderMessage(
            action=order_pb2.MessageType.CREATE_ORDER,
            order_data=order_protobuf
        )

        #  Serialize the OrderMessage to a binary string
        serialized_order_message = order_message.SerializeToString()
        logging.info(f"Serialized Order Message: {serialized_order_message}")

        # Send the serialized message to Kafka
        await producer.send_and_wait(KAFKA_ORDER_CREATED_TOPIC, serialized_order_message)

        # Create a new Order object with additional fields for database storage
        order_dict = order_add.dict()
        order_dict['total_price'] = total_price  # Keep total_price for internal use
        order_dict['status'] = 'pending'
        order_dict['created_at'] = datetime.utcnow()
        order_dict['updated_at'] = datetime.utcnow()

        #  Save the order to the database
        new_order = Order(**order_dict)
        session.add(new_order)
        session.commit()
        session.refresh(new_order)

        # Return the OrderResponse model to the client, including total_price
        return OrderResponse.from_orm(new_order)
        # return OrderResponse.model_validate(new_order)

    except Exception as e:
        logging.error(f"Error during order creation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create the order.")

#list of order
@app.get("/orders/", response_model=List[Order])
def get_order_list(session: Annotated[Session, Depends(get_session)]):
    orders= get_all_orders(session)
    # return orders
    return [OrderResponse.from_orm(order) for order in orders] 

# get order record by id
@app.get("/orders_id/{id}", response_model=Order)
def get_order_id(id: int, session: Annotated[Session, Depends(get_session)]) -> Order:
    order = get_order_by_id(id, session)
    if not order:
        raise HTTPException(status_code=404, detail="Order ID not found")
    return order

# get order record by user id
@app.get("order/user_id/{user_id}", response_model=Order)
def get_order_by_user_id(user_id: int, session: Annotated[Session, Depends(get_session)]) -> Order:
    order = get_order_by_user_id(user_id, session)
    if not order:
        raise HTTPException(status_code=404, detail="Order ID not found")
    return order

#del
@app.delete("/orders/{id}", response_model=dict)
async def delete_order(id: int, session: Annotated[Session, Depends(get_session)],
                       producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]) -> dict:
    # Delete the order
    deleted_order = delete_order_by_id(id, session)
    
    # Create the Protobuf message for deletion
    order_message = order_pb2.OrderMessage(
        action=order_pb2.MessageType.DELETE_ORDER,  # Set the action type for deletion
        order_data=None,  # You can set this to None or omit if you don't need it for deletion
        order_id=id  # Pass the ID of the order to be deleted
    )

    # Serialize the Protobuf message to bytes
    serialized_order_message = order_message.SerializeToString()

    # Produce a message to Kafka after deleting an order
    await producer.send_and_wait(KAFKA_ORDER_DELETED_TOPIC, serialized_order_message)
    logging.info(f"Produced order delete   ID: {id} ")

    return {"message": "Order Deleted Successfully"}

# Fetch product details from the Product Service for update
async def fetch_product_details(product_id: int, client: AsyncClient):
    headers= { "Authorization": "Bearer ur access tpken"}

    response = await client.get(f"http://product_service:8000/products/{product_id}")
    logging.info(f"Product Service Response: {response.status_code}, {response.text}")

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Product not found")

    product_data = response.json()
    return product_data
#update
@app.put("/orders/{id}", response_model=OrderResponse)
async def update_order_id_by_id(id: int,order_data: OrderUpdate,
                                session: Annotated[Session, Depends(get_session)],
                                producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)],
                                client: AsyncClient = Depends(get_http_client)):
    
    # Retrieve the order from the database using its ID
    update_order = session.get(Order, id)
    if not update_order:
        raise HTTPException(status_code=404, detail="Order ID not found")

    update_data = order_data.dict(exclude_unset=True)

    # Check if the quantity is updated and handle price updates accordingly
    if "quantity" in update_data and update_data["quantity"] != update_order.quantity:
        new_quantity = update_data["quantity"]

        # Fetch the product details to get the latest price
        try:
            product_data = await fetch_product_details(update_order.product_id, client)
        except HTTPException as e:
            logging.error(f"Failed to fetch product details: {e.detail}")
            raise

        # Recalculate total price based on the updated quantity and product price
        update_order.total_price = new_quantity * product_data.get("price", 0)
        update_order.quantity = new_quantity  # Update the order quantity

    # Update other fields in the order if provided in the request body
    for key, value in update_data.items():
        setattr(update_order, key, value)

    # Update the updated_at timestamp
    update_order.updated_at = datetime.utcnow()

    # Commit changes to the database
    session.add(update_order)
    session.commit()
    session.refresh(update_order)

    # Create a Protobuf message with the updated order details
    order_message = order_pb2.OrderMessage(
        action=order_pb2.MessageType.UPDATE_ORDER,
        order_data=order_pb2.Order(
            id=update_order.id,
            user_id=update_order.user_id,
            product_id=update_order.product_id,
            product_name=update_order.product_name,
            quantity=update_order.quantity,
            shipping_address=update_order.shipping_address,
            status=update_order.status,
            created_at=update_order.created_at.isoformat(),
            updated_at=update_order.updated_at.isoformat(),
            total_price=update_order.total_price
        ),
        order_id=update_order.id  # Pass the ID of the updated order
    )

    # Serialize the Protobuf message to bytes
    serialized_order_message = order_message.SerializeToString()

    # Send the updated order message to the Kafka topic
    await producer.send_and_wait(KAFKA_ORDER_UPDATED_TOPIC, serialized_order_message)
    logging.info(f"Produced order update message for ID: {update_order.id}")

    return OrderResponse.from_orm(update_order)

