from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: Optional[str] = Field(default=None)  # Email of the user (if applicable)
    user_id: int
    user_name: str
    order_id: str  
    message: str
    sms:str
    phone_number: Optional[str] = Field(default=None) 
    created_at: datetime = Field(default_factory=datetime.utcnow)  

class NotificationResponse(SQLModel):
    id: int
    email: str
    user_id: int
    user_name: str
    order_id: str  
    message: str
    phone_number: str
    created_at: datetime  

class MsgNotification(SQLModel):
    id: int
    user_id: int
    user_name: str
    order_id: str  
    message: str
    phone_number: str
    created_at: datetime  




