from datetime import datetime
from fastapi import HTTPException # type: ignore
from sqlmodel import Session, select # type: ignore
from app.models import Order, OrderCreate, OrderUpdate,OrderResponse

# create new order
def add_new_order(order: OrderCreate, session: Session) -> Order:
    print("Adding Order to ")
    new_order = Order(
        user_id=order.user_id,
        product_id=order.product_id,
        product_name=order.product_name,
        quantity=order.quantity,
        shipping_address=order.shipping_address,
        total_price=order.total_price,
        status="pending"
             
    )
     
    session.add(new_order)
    session.commit()
    session.refresh(new_order)

    return OrderResponse(
        id=new_order.id,
        product_id=new_order.product_id,
        product_name=new_order.product_name,
        user_id=new_order.user_id,
        quantity=new_order.quantity,
        shipping_address=new_order.shipping_address,
        total_price=new_order.total_price,
        status=order.status,
        created_at=new_order.created_at,
        message="Order created successfully"  
          
    )
    
    


# Get All order 
def get_all_orders(session: Session):
    all_orders = session.exec(select(Order)).all()
    return all_orders


# Get a  tracking order by user ID
def get_order_by_user_id(user_id: int, session: Session):
    statement = select(Order).where(Order.user_id == user_id)
    order = session.exec(statement).all()
    if order is None:
        raise HTTPException(status_code=404, detail="Order ID not found")
    return order
# get a tracking order by single id
def get_order_by_id(id: int, session: Session):
    statement = select(Order).where(Order.id == id)
    order = session.exec(statement).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order ID not found")
    return order

# Delete order by ID
def delete_order_by_id(id: int, session: Session):
    
    order = session.exec(select(Order).where(Order.id == id)).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order ID  not found")
    #  Delete the order
    session.delete(order)
    session.commit()
    return {"message": "order item Deleted Successfully"}

 # update
def update_order(id: int, update_data:OrderUpdate, session: Session) -> OrderResponse:
    
    order = session.exec(select(Order).where(Order.id == id)).one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order ID not found")

    for key, value in update_data.items():
        setattr(order, key, value)

    # Set the `updated_at` timestamp
    order.updated_at = datetime.utcnow()
    session.add(order)
    session.commit()
    session.refresh(order)
    return order



