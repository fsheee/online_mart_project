from contextlib import asynccontextmanager
from datetime import datetime
from http import client,status
from typing import AsyncGenerator, Annotated, List, Optional
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
import asyncio
import logging

from app.db import get_session,create_db_and_tables
from app.deps import  get_http_client,get_kafka_producer
from app.models import Payment,PaymentCreate, PaymentResponse,PaymentUpdate
from app.crud.payment_crud import  get_all_payments, get_order_by_single_id, get_payment_by_single_id
from app.proto import payment_pb2
from app.settings import KAFKA_BOOTSTRAP_SERVER, KAFKA_PAYMENT_CREATED_TOPIC, KAFKA_PAYMENT_DELETED_TOPIC,KAFKA_PAYMENT_TOPIC, KAFKA_PAYMENT_UPDATED_TOPIC
from app.consumer.payment_consumer import consume_messages
from httpx import AsyncClient

# import stripe
# from app.config import STRIPE_SECRET_KEY
from app.services.stripe_service import StripeService
from app.services.payfast_service import PayFastService

logging.basicConfig(level=logging.DEBUG)



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logging.info("Lifespan event started...")
    # Initialize the database and create tables
    create_db_and_tables()
    #start kafka consumer task
    task= asyncio.create_task(consume_messages(KAFKA_PAYMENT_TOPIC,KAFKA_BOOTSTRAP_SERVER))
      
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
            "url": "http://127.0.0.1:8002", 

            "description": "Development Server"
        }
    ]
)


@app.get("/")
def read_root():
    return {"Payment": "Service"}

# retrive order data to check payment

async def get_order_status(order_id: int):
    order_response = await client.get(f"http://order_service:8000/order/{order_id}")
    logging.info(f"Order Service Response: {order_response.status_code}, {order_response.text}")
    
    if order_response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order ID does not exist")
    
    return order_response.json()


 

async def ment(payment_add: PaymentCreate,
               session: Annotated[Session, Depends(get_session)],
               producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)],
               client: AsyncClient = Depends(get_http_client)):
    
    try:
        # Verify order status
        order_data = await get_order_status(payment_add.order_id, client)

        # Default status to pending
        payment_status = "pending"
        
        # Branch logic based on payment method
        if payment_add.payment_method == "stripe":
            # Use StripeService to create the payment intent
            try:
                intent = StripeService.create_payment_intent(payment_add.amount, payment_add.currency)
                payment_status = "confirmed" if intent['status'] == 'succeeded' else "failed"
            except Exception as e:
                logging.error(f"Stripe payment failed: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stripe payment failed.")
        
        elif payment_add.payment_method == "payfast":
            # Use PayFastService to create the payment (You must implement this service)
            payfast_service = PayFastService()
            try:
                payfast_response = payfast_service.create_payment(payment_add.amount, payment_add.currency, "return_url", "cancel_url")
                payment_status = "confirmed" if payfast_response['status'] == 'success' else "failed"
            except Exception as e:
                logging.error(f"PayFast payment failed: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="PayFast payment failed.")
        
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment method.")
        
        # Create a protobuf Payment object
        payment_protobuf = payment_pb2.Payment(
            user_id=payment_add.user_id,
            order_id=payment_add.order_id,
            payment_method=payment_add.payment_method,
            amount=payment_add.amount,
            currency=payment_add.currency,
            status=payment_status,
        )

        # Create a PaymentMessage for Kafka
        payment_message = payment_pb2.PaymentMessage(
            message_type=payment_pb2.MessageType.CREATE_PAYMENT,
            payment_data=payment_protobuf
        )
        
        # Serialize the PaymentMessage to a binary string
        serialized_payment_message = payment_message.SerializeToString()
        logging.info(f"Serialized Payment Message: {serialized_payment_message}")

        # Send the serialized message to Kafka
        await producer.send_and_wait(KAFKA_PAYMENT_CREATED_TOPIC, serialized_payment_message)

        # Create a new Payment object for the database
        new_payment = Payment(
            user_id=payment_add.user_id,
            order_id=payment_add.order_id,
            payment_method=payment_add.payment_method,
            amount=payment_add.amount,
            currency=payment_add.currency,
            status=payment_status,
            created_at=datetime.utcnow(),  # Store as timezone-aware datetime
            updated_at=datetime.utcnow(),
        )
        
        # Save the payment to the database
        session.add(new_payment)
        session.commit()
        session.refresh(new_payment)

        return PaymentResponse.from_orm(new_payment)

    except Exception as e:
        logging.error(f"Error during payment creation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create the payment.")
        

    
   
#list
@app.get("/payments/", response_model=List[Payment])
async def read_all_paymnets(session: Annotated[Session, Depends(get_session)] ) -> List[Payment]:
    payments = get_all_payments(session)
    return payments


# Search payment by ID
@app.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment_by_id(payment_id: int, session: Annotated[Session, Depends(get_session)]):
   
    payment = get_payment_by_single_id(payment_id, session)
    
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment ID not found")
    
    return payment

# # Search order by ID
# @app.get("/payments/{order_id}", response_model=PaymentResponse)
def get_payment_by_order_id(order_id: int, session: Annotated[Session, Depends(get_session)]):
    order = get_order_by_single_id(order_id, session)
    
    if order is None:
        raise HTTPException(status_code=404, detail="Order ID not found")
    
    return order
#update
@app.put("/payments/update/{order_id}", response_model=PaymentResponse)
async def update_payment(payment_update: PaymentUpdate,
                         session: Annotated[Session, Depends(get_session)],
                         producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):
    try:
        # Fetch the payment record from the database
        payment = session.get(Payment, payment_update.order_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Update the fields with new data
        payment.amount = payment_update.amount or payment.amount
        payment.currency = payment_update.currency or payment.currency
        payment.status = payment_update.status or payment.status
        payment.updated_at = datetime.utcnow()

        # Save the updated payment to the database
        session.commit()
        session.refresh(payment)

        # Create a Protobuf Payment object with the updated data
        payment_protobuf = payment_pb2.Payment(
            user_id=payment.user_id,
            order_id=payment.order_id,
            payment_method=payment.payment_method,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status
        )

        # Create a Protobuf PaymentMessage for Kafka
        payment_message = payment_pb2.PaymentMessage(
            message_type=payment_pb2.MessageType.UPDATE_PAYMENT,
            payment_data=payment_protobuf
        )

        # Serialize the PaymentMessage to a binary string
        serialized_message = payment_message.SerializeToString()
        logging.info(f"Serialized Update Payment Message: {serialized_message}")

        # Send the message to Kafka
        await producer.send_and_wait(KAFKA_PAYMENT_UPDATED_TOPIC, serialized_message)

        return PaymentResponse.from_orm(payment)

    except Exception as e:
        logging.error(f"Error updating payment: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update the payment.")

# del

@app.delete("/payments/{order_id}", response_model=PaymentResponse)
async def delete_payment_endpoint( order_id: int,
                                   session: Annotated[Session, Depends(get_session)],
                                    producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):
    try:
        # Fetch the payment record from the database
        payment = session.get(Payment, order_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Delete the payment record from the database
        session.delete(payment)
        session.commit()

        # Create a Protobuf Payment object with the deleted payment data
        payment_protobuf = payment_pb2.Payment(
            user_id=payment.user_id,
            order_id=payment.order_id,
            payment_method=payment.payment_method,
            amount=payment.amount,
            currency=payment.currency,
            status="deleted"
        )

        # Create a Protobuf PaymentMessage for Kafka
        payment_message = payment_pb2.PaymentMessage(
            message_type=payment_pb2.MessageType.DELETE_PAYMENT,
            payment_data=payment_protobuf
        )

        # Serialize the PaymentMessage to a binary string
        serialized_message = payment_message.SerializeToString()
        logging.info(f"Serialized Delete Payment Message: {serialized_message}")

        # Send the message to Kafka
        await producer.send_and_wait(KAFKA_PAYMENT_DELETED_TOPIC, serialized_message)

        return {"message": "Payment deleted successfully"}

    except Exception as e:
        logging.error(f"Error deleting payment: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete the payment.")
