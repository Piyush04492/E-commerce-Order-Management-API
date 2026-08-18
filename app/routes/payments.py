from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.schemas.payment import PaymentResponse, PaymentSimulationRequest
from app.services.payment_service import PaymentService
from app.services.order_service import OrderService
from app.models.user import User
from app.routes.deps import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/", response_model=PaymentResponse, status_code=201)
def simulate_payment(
    order_id: int,
    payment_data: PaymentSimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulates a payment gate interface.
    Validates ownership of the order, processes mock success or failure,
    and triggers corresponding inventory deductions or reservation releases.
    """
    order = OrderService.get_order_by_id(db, order_id)
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You cannot submit payments for orders you do not own."
        )
    
    return PaymentService.simulate_payment(
        db=db,
        order_id=order_id,
        payment_method=payment_data.payment_method,
        simulate_success=payment_data.simulate_success
    )

@router.get("/{order_id}", response_model=List[PaymentResponse])
def get_payments(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves payment ledger details for a specific order.
    Customers see their own payments; Admins see all.
    """
    order = OrderService.get_order_by_id(db, order_id)
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to access payment records for this order."
        )
    return PaymentService.get_payments_for_order(db, order_id)
