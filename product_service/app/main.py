from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, List
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from aiokafka import AIOKafkaProducer
import asyncio
import logging

from app.db import create_db_and_tables, get_session
from app import deps
from app.models import Product, ProductAdd, ProductUpdate
from app.crud.prd_crud import add_new_product, update_product_by_id, delete_product_by_id, get_product_by_id, get_all_products
from app.consumer.prd_consumer import consume_messages
from app.proto import product_pb2
from app.settings import KAFKA_PRODUCT_TOPIC,BOOTSTRAP_SERVER

logging.basicConfig(level=logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_db_and_tables()
    #consume msg
    task = asyncio.create_task(consume_messages(KAFKA_PRODUCT_TOPIC,BOOTSTRAP_SERVER))
    try:
        yield
    finally:
        task.cancel()
        await task

app = FastAPI(
    lifespan=lifespan,
    title="Kafka With FastAPI",
    version="0.0.1",
    servers=[
        {
            "url": "http://127.0.0.1:8005",
            "description": "Development Server"
        }
    ]
)


@app.get("/")
def read_root():
    return {"Product": "Service"}

#create
@app.post("/products/", response_model=Product)
async def create_product(product: ProductAdd,  session: Annotated[Session, Depends(get_session)],
                        producer: Annotated[AIOKafkaProducer, 
                           Depends(deps.get_kafka_producer)]) -> Product:
    try:
        # Create the Product message
        product_protobuf = product_pb2.Product(
            product_name=product.product_name,
            description=product.description,
            price=product.price,
            expiry=product.expiry or "",
            brand=product.brand or "",
            category=product.category
        )

        # Create the ProductMessage with the operation type
        product_message = product_pb2.ProductMessage(
            message_type=product_pb2.OperationType.CREATE,
            product_data=product_protobuf
        )

        # Serialize the ProductMessage
        serialized_product_message = product_message.SerializeToString()

        logging.info(f"Serialized Product Message: {serialized_product_message}")

        # Produce message to Kafka
        await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product_message)

        # Add the product to the database
        new_product = add_new_product(product, session)
        return new_product

    except Exception as e:
        logging.error(f"Error in create_product: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# search by ID
@app.get("/products/{product_id}", response_model=Product)
def read_product(product_id: int,session: Annotated[Session, Depends(get_session)]) -> Product:
    product =  get_product_by_id(product_id, session)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# list of product
@app.get("/products/", response_model=List[Product])
def read_all_products(session: Annotated[Session, Depends(get_session)]) -> List[Product]:
    products = get_all_products(session) 
    return products

#update 
@app.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: int, product: ProductUpdate, session: Annotated[Session, Depends(get_session)],
                        producer: Annotated[AIOKafkaProducer, Depends(deps.get_kafka_producer)])-> Product:
    # Update the product in the database
    updated_product = update_product_by_id(product_id, product, session)  
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Serialize and produce message
    product_protobuf = product_pb2.Product(
        product_id=updated_product.product_id,
        product_name=updated_product.product_name,
        description=updated_product.description,
        price=updated_product.price,
        expiry=updated_product.expiry or "",
        brand=updated_product.brand or "",
        category=updated_product.category
    )

    logging.info(f"Product Protobuf for update: {product_protobuf}")

    # Create the ProductMessage with the operation type set to EDIT
    product_message = product_pb2.ProductMessage(
        message_type=product_pb2.OPERATIONType.EDIT,
        product_data=product_protobuf
    )

    # Serialize the product message
    serialized_product_message = product_message.SerializeToString()  # Serialize the message

    logging.info(f"Serialized Product Message: {serialized_product_message}")

    # Produce the message to Kafka
    try:
        await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product_message)
        logging.info("Product update message sent to Kafka successfully.")
    except Exception as e:
        logging.error(f"Error sending product update message to Kafka: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message to Kafka")

    return updated_product

# del
@app.delete("/products/{product_id}", response_model=dict)
async def delete_product(product_id: int, session: Annotated[Session, Depends(get_session)],
    producer: Annotated[AIOKafkaProducer, Depends(deps.get_kafka_producer)]) -> dict:
    # Retrieve the product before deletion
    product = session.exec(select(Product).where(Product.product_id == product_id)).one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Serialize and produce the product deletion message
    product_protobuf = product_pb2.Product(
        product_id=product.product_id,
        product_name=product.product_name,
        description=product.description,
        price=product.price,
        expiry=product.expiry or "",
        brand=product.brand or "",
        category=product.category
    )

    logging.info(f"Product to be deleted: {product_protobuf}")

    # Create the ProductMessage with the operation type set to DELETE
    product_message = product_pb2.ProductMessage(
        message_type=product_pb2.OperationType.DELETE,  
        product_data=product_protobuf
    )

    # Serialize the product message
    serialized_product_message = product_message.SerializeToString()
    logging.info(f"Serialized Product Message for deletion: {serialized_product_message}")

    # Send the message to Kafka
    try:
        await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product_message)
        logging.info("Product deletion message sent to Kafka successfully.")
    except Exception as e:
        logging.error(f"Error sending product deletion message to Kafka: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message to Kafka")

    # Delete the product
    delete_product_by_id(product_id, session)

    return {"message": "Product Item Deleted Successfully"}
 
