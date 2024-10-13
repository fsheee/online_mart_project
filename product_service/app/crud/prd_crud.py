from fastapi import HTTPException # type: ignore
from sqlmodel import Session, select # type: ignore
from app.models import Product,ProductAdd,  ProductResponse,ProductUpdate
# Add a New Product 

def add_new_product(product: ProductAdd, session: Session) -> ProductResponse:
    print("Adding Product to Database")
    new_product = Product(
        product_name=product.product_name,
        description=product.description,
        price=product.price,
        expiry=product.expiry,
        brand=product.brand,
        # stock=product.stock,
        # weight=product.weight,
        category=product.category
    )
    session.add(new_product)
    session.commit()
    session.refresh(new_product)
    
    # Create and return ProductResponse object
    return ProductResponse(
        product_id=new_product.product_id,
        product_name=new_product.product_name,
        description=new_product.description,
        price=new_product.price,
        expiry=new_product.expiry,
        brand=new_product.brand,
        # weight=new_product.weight,
        category=new_product.category
        # message="Product created successfully"   
    )
    


# Get All Products 
def get_all_products(session: Session):
    all_products = session.exec(select(Product)).all()
    return all_products

# Get a Product by ID
def get_product_by_id(product_id: int, session: Session):
    product = session.exec(select(Product).where(Product.product_id == product_id)).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product ID not found")
    return product

# Delete Product by ID
def delete_product_by_id(product_id: int, session: Session):
    
    product = session.exec(select(Product).where(Product.product_id == product_id)).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product ID not found")
    #  Delete the Product
    session.delete(product)
    session.commit()
    # return {"message": "Product Item Deleted Successfully"}
    return product


# # Validate Product by ID return none
# def validate_product_by_id(product_id: int, session: Session) -> Product | None:
#     product = session.exec(select(Product).where(Product.id == product_id)).one_or_none()
    # return product


def update_product_by_id(product_id: int, update_product: ProductUpdate, session: Session) -> Product: 
    print(f"Updating product with ID: {product_id}")
    product = session.exec(select(Product).where(Product.product_id == product_id)).one_or_none()
    if product is None:
        print(f"Product with ID {product_id} not found")
        raise HTTPException(status_code=404, detail="Product ID not found")
    
    update_data = update_product.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    session.add(product)
    session.commit()
    session.refresh(product)
    print(f"Product with ID {product_id} updated successfully")
    return product



