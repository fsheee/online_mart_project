
import requests  # type: ignore
from fastapi import HTTPException
from sqlmodel import Session, select
from app.models import Inventory, InventoryCreate, InventoryUpdate

def create_inventory(inventory_item: InventoryCreate, session: Session):
    validate_product_id(inventory_item.product_id)
    # Create an inventory instance using model_validate
    inventory = Inventory.model_validate(inventory_item.dict())
    # inventory = Inventory.from_orm(inventory_item)
    session.add(inventory)
    session.commit()
    session.refresh(inventory)
    return inventory

# fetch product_id  # validate to inventory(id) table
def validate_product_id(product_id: int):
    try:
        response = requests.get(f"http://product_service:8000/products/{product_id}")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Product ID {product_id} validation failed: {e}")


#list of inventory
def get_inventory_list(session: Session):
    all_inventory = session.exec(select(Inventory)).all()
    return all_inventory


# Get an inventory by ID
def get_inventory_by_id(id: int, session: Session):
    product = session.exec(select(Inventory).where(Inventory.id == id)).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Inventory ID not found")
    return product



# Update Inventory 
def update_inventory_item_by_id(product_id: int, updated_item: InventoryUpdate, session: Session) -> Inventory: 
    print(f"Updating inventory with productID: {product_id}")
    inventory = session.exec(select(Inventory).where(Inventory.product_id == product_id)).one_or_none()
    if inventory is None:
        print(f"inventory with ID {id} not found")
        raise HTTPException(status_code=404, detail="inventory ID not found")
    
    update_inventory_item = updated_item.dict(exclude_unset=True)
    for key, value in update_inventory_item.items():
        setattr(inventory, key, value)
    
    session.add(inventory)
    session.commit()
    session.refresh(inventory)
    return inventory





# del by id
def delete_inventory_by_id(id: int, session: Session):
    
    inventory = session.exec(select(Inventory).where(Inventory.id == id)).one_or_none()
    if inventory is None:
        raise HTTPException(status_code=404, detail="Inventory ID not found")
    #  Delete the inventory
    session.delete(inventory)
    session.commit()
    return {"message": "Product Item Deleted Successfully"}
    # return inventory

