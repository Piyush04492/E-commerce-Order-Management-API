from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.schemas.order import OrderCheckout, OrderResponse, OrderStatusUpdate
from app.services.order_service import OrderService
from app.models.user import User
from app.routes.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/checkout", response_model=OrderResponse, status_code=201)
def checkout(
    checkout_data: OrderCheckout,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes transaction-safe order placement.
    Converts CartItems into OrderItems with frozen pricing, reserves stock, and clears the cart.
    Restricted to Customers.
    """
    if current_user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customer accounts can initiate checkouts."
        )
    return OrderService.checkout(db, current_user.id, checkout_data.shipping_address)

@router.get("/", response_model=List[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists orders:
    - Customers receive their personal order history.
    - Admins receive a list of all system orders.
    """
    if current_user.role == "admin":
        return OrderService.get_all_orders(db)
    return OrderService.get_user_orders(db, current_user.id)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a single order by ID.
    Customers can only view their own orders; Admins can view any order.
    """
    order = OrderService.get_order_by_id(db, order_id)
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not own this order."
        )
    return order

@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Updates status for an order.
    Runs state-machine validations and settles or releases inventory.
    Restricted to Admins.
    """
    return OrderService.update_order_status(db, order_id, status_data.status)

@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Allows a customer to self-cancel an order.
    Only permitted if the order is still in 'PENDING' state.
    """
    return OrderService.cancel_order(db, order_id, current_user.id)
