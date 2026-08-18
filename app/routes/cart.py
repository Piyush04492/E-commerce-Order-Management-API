from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.cart import CartResponse, CartItemAdd, CartItemUpdate
from app.services.cart_service import CartService
from app.models.user import User
from app.routes.deps import get_current_user

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])

def enforce_customer_role(user: User):
    """Utility dependency helper to restrict access to customers."""
    if user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customer accounts can maintain shopping carts."
        )

@router.get("/", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Retrieve items in the current user's shopping cart."""
    enforce_customer_role(current_user)
    return CartService.get_or_create_cart(db, current_user.id)

@router.post("/items", response_model=CartResponse)
def add_item_to_cart(
    item_data: CartItemAdd, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Add a product to the cart.
    Checks that the quantity requested is within available stock limits.
    """
    enforce_customer_role(current_user)
    return CartService.add_item_to_cart(db, current_user.id, item_data)

@router.put("/items/{cart_item_id}", response_model=CartResponse)
def update_cart_item(
    cart_item_id: int, 
    update_data: CartItemUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Update quantity of an item in the cart, checking stock limits."""
    enforce_customer_role(current_user)
    return CartService.update_cart_item(db, current_user.id, cart_item_id, update_data.quantity)

@router.delete("/items/{cart_item_id}", response_model=CartResponse)
def delete_cart_item(
    cart_item_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Remove an item from the shopping cart."""
    enforce_customer_role(current_user)
    return CartService.delete_cart_item(db, current_user.id, cart_item_id)
