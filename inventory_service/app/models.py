

from sqlmodel import SQLModel, Field
from typing import Optional


class Inventory(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    product_id: int
    quantity: int
    status_stock: str

class InventoryCreate(SQLModel):
    product_id: int
    quantity: int
    status_stock: str

class InventoryUpdate(SQLModel):
    quantity: int
    status_stock: str

class InventoryResponse(SQLModel):
    id: int
    product_id: int
    quantity: int
    status_stock: str