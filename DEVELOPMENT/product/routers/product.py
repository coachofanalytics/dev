from fastapi import status, Response, HTTPException, APIRouter
from fastapi.params import Depends
from  product.database import get_db
from sqlalchemy.orm import Session
from product import schemas, models
from typing import List
from product.routers.login import get_current_user


router = APIRouter(
    tags=['Products'],
    prefix="/product"
)

# Add new product to the products database table --> just like a create view
@router.post('/', status_code=status.HTTP_201_CREATED)
def add(request: schemas.Product, db: Session = Depends(get_db),  current_user:schemas.User = Depends(get_current_user)):
    new_product = models.Product(
        name=request.name,
        description=request.description,
        price=request.price,
        user_id = 1
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return request


# Fetch all items from the products database table --> just like a list view
@router.get('/', response_model=List[schemas.DisplayProduct])
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return products


# Fetch an item from the products database table based on the id
@router.get('/{id}', response_model=schemas.DisplayProduct)
def get_one_product(id, response:Response, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Product Not Found") 
    
    return product


# Update an item from the products database tabke based on the id.
@router.put('/{id}')
def update_product(id, request: schemas.Product, db: Session=Depends(get_db),  current_user:schemas.User = Depends(get_current_user)):
    product = db.query(models.Product).filter(models.Product.id == id)

    if not product.first():
        pass
    product.update(request.dict())
    db.commit()
    return {'Product Successfully Updated'}


# Delete an item from the products database tabke based on the id.
@router.delete('/{id}')
def delete_product(id, db: Session = Depends(get_db),  current_user:schemas.User = Depends(get_current_user)):
    db.query(models.Product).filter(models.Product.id == id).delete(synchronize_session=False)
    db.commit()
    return {'Product Deleted'}

