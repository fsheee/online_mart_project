from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Payment(SQLModel, table=True):
    payment_id: Optional[int] = Field(default=None, primary_key=True, index=True)
    order_id: int 
    user_id: int 
    amount: float 
    currency: str 
    payment_method: str = Field(..., description="The payment method used, e.g., 'stripe', 'payfast'")
    status: str = Field(default="pending", description="The status of the payment, e.g., 'pending', 'completed'")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="The time the payment was created")
    updated_at: Optional[datetime] = Field(default=None, description="The time the payment was last updated")

    
class PaymentCreate(SQLModel):
    order_id: int
    user_id: int
    amount: float
    currency: str
    payment_method: str    

class PaymentUpdate(SQLModel):
    status: Optional[str] = None

class PaymentResponse(SQLModel):
    payment_id: int
    order_id: int
    user_id: int
    amount: float
    currency: str
    payment_method: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None        