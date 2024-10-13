from datetime import datetime
from typing import Optional
from fastapi import HTTPException # type: ignore
from sqlmodel import Session, select # type: ignore
from app.models import PaymentCreate,Payment,PaymentUpdate,PaymentResponse

# Create new payment
def add_new_payment(payment: PaymentCreate, session: Session) -> dict:
    print("Adding Payment to Database")
    new_payment = Payment(
        order_id=payment.order_id,
        user_id=payment.user_id,
        amount=payment.amount,
        currency=payment.currency,
        payment_method=payment.payment_method,
        
    )
     
    session.add(new_payment)
    session.commit()
    session.refresh(new_payment)

    return {
        "message": "Payment created successfully",
        "payment": PaymentResponse(
            payment_id=new_payment.payment_id,
            amount=new_payment.amount,
            currency=new_payment.currency,
            payment_status=new_payment.payment_status,
            payment_method=new_payment.payment_method,
            created_at=new_payment.created_at,
            updated_at=new_payment.updated_at,
        )
    }
    

# Get All payments
def get_all_payments(session: Session):
    all_payments = session.exec(select(Payment)).all()
    return all_payments

# Get a payment by ID
def get_payment_by_single_id(payment_id: int, session: Session) -> PaymentResponse:
    statement = select(Payment).where(Payment.payment_id == payment_id)
    payment = session.exec(statement).one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment ID not found")
    return payment

def get_order_by_single_id(order_id: int, session: Session) -> PaymentResponse:
    statement = select(Payment).where(Payment.order_id == order_id)
    payment = session.exec(statement).one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Order ID not found")
    return payment

# Delete payment by ID
def delete_payment_by_id(payment_id: int, session: Session):
    
    payment = session.exec(select(Payment).where(Payment.payment_id == payment_id)).one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment ID  not found")
    #  Delete the order
    session.delete(payment)
    session.commit()
    return {"message": "  Deleted Successfully"}
 
def update_payment(payment_id: int, payment_data: PaymentUpdate, session: Session) -> PaymentResponse:
    """Update a payment record."""
    payment = session.get(Payment, payment_id)
    if payment:
        if payment_data.status is not None:
            payment.status = payment_data.status
        # payment.updated_at = datetime.utcnow()  
        session.add(payment)
        session.commit()
        session.refresh(payment)
    return payment

# # update


# def update_payment(payment_id: int, payment_update: PaymentUpdate, session: Session) -> PaymentRead:
    
    
#     statement = select(Payment).where(Payment.payment_id == payment_id)
#     payment = session.exec(statement).one_or_none()
    
#     if payment is None:
#         raise HTTPException(status_code=404, detail="Payment ID not found")
    
#     # Exclude unset fields from the update
#     update_data = payment_update.dict(exclude_unset=True)
    
#     # Update the payment attributes
#     for key, value in update_data.items():
#         setattr(payment, key, value)

#     session.add(payment)
#     session.commit()
#     session.refresh(payment)
    
#     return PaymentRead(
#         payment_id=payment.payment_id,
#         amount=payment.amount,
#         currency=payment.currency,
#         payment_status=payment.payment_status,
#         payment_method=payment.payment_method,
#         transaction_id=payment.transaction_id,
#         created_at=payment.created_at,
#     )


# def update_payment( payment_id: int, payment_data: PaymentUpdate,session: Session):
    
#     statement = select(Payment).where(Payment.payment_id == payment_id)
    
    
#     payment = session.exec(statement).one_or_none() 
    
#     if payment:
#         # Update the payment fields
#         payment.amount = payment_data.amount
#         payment.currency = payment_data.currency
#         payment.payment_status = payment_data.payment_status
#         payment.payment_method = payment_data.payment_method
        
#         # Commit the changes
#         session.add(payment)
#         session.commit()
#         session.refresh(payment)

#     return payment



# def update_payment(session: Session, payment_id: int, payment_data: PaymentUpdate):
#     # Query to find the payment record
#     statement = select(Payment).where(Payment.id == id)
#     payment = session.exec(statement).one_or_none()
    
#     if not payment:
#         return None  
    
    
#     if payment_data.amount is not None:
#         payment.amount = payment_data.amount
    
#     if payment_data.currency is not None:
#         payment.currency = payment_data.currency
    
#     if payment_data.payment_status is not None:
#         payment.payment_status = payment_data.payment_status
    
#     if payment_data.payment_method is not None:
#         payment.payment_method = payment_data.payment_method
    
#     # if payment_data.transaction_id is not None:
#     #     payment.transaction_id = payment_data.transaction_id
    
#     # Commit the session to save changes
#     session.add(payment)
#     session.commit()
#     session.refresh(payment)  # Refresh the object to get the latest data

#     return payment
