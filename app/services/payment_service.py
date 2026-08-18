import uuid
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.payment import Payment
from app.models.order import Order
from app.services.order_service import OrderService

class PaymentService:
    """
    Simulates financial payment processing.
    Updates corresponding order and inventory state depending on payment success or failure.
    """

    @staticmethod
    def simulate_payment(
        db: Session, 
        order_id: int, 
        payment_method: str, 
        simulate_success: bool
    ) -> Payment:
        # Retrieve the order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Order not found."
            )

        # We can only pay for PENDING orders
        if order.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot pay for order that is already in {order.status} state."
            )

        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        payment_status = "SUCCESS" if simulate_success else "FAILED"

        try:
            # Create payment record
            payment = Payment(
                order_id=order_id,
                amount=order.total_amount,
                payment_method=payment_method,
                status=payment_status,
                transaction_id=transaction_id
            )
            db.add(payment)
            db.flush()

            # Settle the corresponding Order status and Inventory allocations
            if simulate_success:
                # Transits PENDING -> CONFIRMED, which deducts physical inventory and releases reservations
                OrderService.update_order_status(db, order_id=order_id, new_status="CONFIRMED")
            else:
                # Transits PENDING -> CANCELLED, which releases reservations (physical inventory is untouched)
                OrderService.update_order_status(db, order_id=order_id, new_status="CANCELLED")

            db.commit()
            db.refresh(payment)
            return payment

        except Exception as e:
            db.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment processing failed: {str(e)}"
            )

    @staticmethod
    def get_payments_for_order(db: Session, order_id: int) -> List[Payment]:
        """Fetch payment records associated with a specific order."""
        return db.query(Payment).filter(Payment.order_id == order_id).all()
