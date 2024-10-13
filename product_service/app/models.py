from sqlmodel import SQLModel, Field
from typing import Optional



class Product(SQLModel, table=True):
    product_id: Optional[int] = Field(default=None, primary_key=True)
    product_name: str = Field(index=True)
    description: str
    price: float
    expiry: Optional[str] = None
    brand: Optional[str] = None
    category: str


class ProductResponse(SQLModel):
    product_id: int
    product_name: str
    description: str
    price: int
    expiry: Optional[str] = None
    brand: Optional[str] = None
    # stock: int
    category: str
    # weight: Optional[float] = None
    # message:str




class ProductAdd(SQLModel):
    product_name: str
    description: str
    price: int
    expiry: Optional[str] = None
    brand: Optional[str] = None
    # weight: Optional[float] = None
    # stock: int
    category: str

class ProductUpdate(SQLModel):
    product_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    expiry: Optional[str] = None
    brand: Optional[str] = None
    # stock: Optional[int] = None
    # weight: Optional[float] = None
    category: Optional[str] = None
