from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService
from app.models.user import User
from app.routes.deps import get_current_admin

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=List[ProductResponse])
def get_products(
    category: Optional[str] = Query(None, description="Filter products by category name (case-insensitive)"),
    min_price: Optional[float] = Query(None, description="Lower price threshold (inclusive)"),
    max_price: Optional[float] = Query(None, description="Upper price threshold (inclusive)"),
    search: Optional[str] = Query(None, description="Match keywords in product name or description"),
    sort_by: str = Query("id", description="Field to sort by (e.g. 'price', 'name', 'id')"),
    sort_order: str = Query("asc", description="Sort order: 'asc' or 'desc'"),
    page: int = Query(1, ge=1, description="Page number to fetch"),
    limit: int = Query(20, ge=1, le=100, description="Number of products per page"),
    db: Session = Depends(get_db)
):
    """
    Browse catalog products with full query support.
    Supports filtration (category, price limits), keyword searches, sorting, and pagination.
    """
    return ProductService.get_products_filtered(
        db=db,
        category=category,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit
    )

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Fetch details of a single product."""
    return ProductService.get_product_by_id(db, product_id)

@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    product_data: ProductCreate, 
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    """
    Adds a new product to the catalog.
    Automatically initializes its corresponding inventory record.
    Restricted to Admins.
    """
    return ProductService.create_product(db, product_data)

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, 
    product_data: ProductUpdate, 
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    """
    Modifies details of an existing product.
    Restricted to Admins.
    """
    return ProductService.update_product(db, product_id, product_data)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int, 
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    """
    Removes a product from the catalog.
    Restricted to Admins.
    """
    ProductService.delete_product(db, product_id)
    return None
