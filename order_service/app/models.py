from pydantic import BaseModel, ConfigDict
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    product_id: int
    product_name: str
    quantity: int
    shipping_address: str
    status: str = "pending"  # Default status
    total_price: Optional[float]  # To be set in the backend
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)



class OrderCreate(SQLModel):
    user_id: int
    product_id: int
    product_name: str
    quantity: int
    shipping_address: str

class OrderUpdate(SQLModel):
    # product_name:str
    shipping_address: Optional[str] = None
    quantity: Optional[int] = None
    # total_price: Optional[float] = None
    
    


# Response schema for returning order details (including total_price)
class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    product_name: str
    quantity: int
    shipping_address: str
    status: str
    total_price: float  # Include total_price in the response
    created_at: str
    updated_at: str

    # class Config:
    #     orm_mode = True  #  work with ORM objects
    #Enable ORM parsing in the model configuration
    # model_config = ConfigDict(from_attributes=True)  # New in Pydantic v2

    @classmethod
    def from_orm(cls, order) -> "OrderResponse":
        return cls(
            id=order.id,
            user_id=order.user_id,
            product_id=order.product_id,
            product_name=order.product_name,
            quantity=order.quantity,
            shipping_address=order.shipping_address,
            total_price=order.total_price,
            status=order.status,
            created_at=order.created_at.isoformat(),  # Convert to ISO string
            updated_at=order.updated_at.isoformat(),  # Convert to ISO string
        )
    
    """The from_orm method is typically a class method in your response schema 
    that accepts an ORM object
        (like an instance of Order) and maps its attributes to the schema fields."""

