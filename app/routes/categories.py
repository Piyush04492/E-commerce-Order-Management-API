from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.schemas.category import CategoryCreate, CategoryResponse
from app.services.product_service import ProductService
from app.models.user import User
from app.routes.deps import get_current_admin

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Browse all product categories."""
    return ProductService.get_all_categories(db)

@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(
    category_data: CategoryCreate, 
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    """
    Creates a new product category.
    Restricted to Admins.
    """
    return ProductService.create_category(db, category_data)
