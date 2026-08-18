from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.utils.validators import is_valid_status_transition
from app.services.cart_service import CartService

class OrderService:
    """
    Core business logic for Checkout and Order management.
    Good interview points:
    1. Checkout is fully transactional. If one step fails, the entire order collapses, protecting inventory.
    2. Available stock is checked and reserved during checkout (reserves stock without deducting physical inventory).
    3. Unit price is copied to order items to preserve history.
    4. State machine dictates inventory settlement:
       - PENDING -> CONFIRMED: Deduct physical quantity and release reservation (since payment succeeded).
       - PENDING -> CANCELLED: Release reservation only (physical stock was never deducted).
       - CONFIRMED/PROCESSING -> CANCELLED: Restock physical quantity (since it was deducted).
    """

    @classmethod
    def checkout(cls, db: Session, user_id: int, shipping_address: str) -> Order:
        # 1. Fetch user's cart
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Your cart is empty."
            )

        # We will use SQLAlchemy's transaction context.
        # If any exception occurs inside this block, we roll back manually to be safe.
        try:
            total_amount = 0.0
            order_items_to_create = []
            inventories_to_update = []

            for cart_item in cart.items:
                product = db.query(Product).filter(Product.id == cart_item.product_id).first()
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product with ID {cart_item.product_id} no longer exists."
                    )

                inventory = db.query(Inventory).filter(Inventory.product_id == product.id).first()
                if not inventory:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Inventory record missing for product {product.name}."
                    )

                # Check if enough stock exists: quantity - reserved_quantity
                if inventory.available_quantity < cart_item.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock for {product.name}. Available: {inventory.available_quantity}, requested: {cart_item.quantity}"
                    )

                # Reserve stock (increment reserved_quantity)
                inventory.reserved_quantity += cart_item.quantity
                inventories_to_update.append(inventory)

                # Calculate item subtotals
                subtotal = product.price * cart_item.quantity
                total_amount += subtotal

                # Prepare the OrderItem record, freezing the price
                order_item = OrderItem(
                    product_id=product.id,
                    quantity=cart_item.quantity,
                    unit_price=product.price,
                    subtotal=subtotal
                )
                order_items_to_create.append(order_item)

            # Create the master Order record in PENDING state
            order = Order(
                user_id=user_id,
                total_amount=total_amount,
                status="PENDING",
                shipping_address=shipping_address
            )
            db.add(order)
            db.flush()  # Generates the order.id so we can link OrderItems

            # Link order items to this order
            for item in order_items_to_create:
                item.order_id = order.id
                db.add(item)

            # Clear the shopping cart
            db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

            db.commit()
            db.refresh(order)
            return order

        except Exception as e:
            db.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Checkout failed: {str(e)}"
            )

    @staticmethod
    def get_user_orders(db: Session, user_id: int) -> List[Order]:
        """Fetch all orders placed by a specific user."""
        return db.query(Order).filter(Order.user_id == user_id).all()

    @staticmethod
    def get_order_by_id(db: Session, order_id: int) -> Order:
        """Fetch a specific order by ID."""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Order not found."
            )
        return order

    @classmethod
    def update_order_status(cls, db: Session, order_id: int, new_status: str) -> Order:
        """
        Updates the order status, executing inventory settlements based on FSM rules.
        """
        order = cls.get_order_by_id(db, order_id)
        current_status = order.status
        new_status = new_status.upper()

        if not is_valid_status_transition(current_status, new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid transition from {current_status} to {new_status}."
            )

        try:
            # 1. PENDING -> CONFIRMED (Payment Succeeded)
            # Physical stock is deducted, reserved stock is released.
            if current_status == "PENDING" and new_status == "CONFIRMED":
                for item in order.items:
                    inventory = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
                    if inventory:
                        inventory.quantity -= item.quantity
                        inventory.reserved_quantity -= item.quantity

            # 2. PENDING -> CANCELLED (Payment failed or manual cancellation)
            # Physical stock is untouched, reserved stock is released.
            elif current_status == "PENDING" and new_status == "CANCELLED":
                for item in order.items:
                    inventory = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
                    if inventory:
                        inventory.reserved_quantity -= item.quantity

            # 3. CONFIRMED / PROCESSING -> CANCELLED (Restock items)
            # Physical stock is added back (since it was deducted on confirmation).
            elif current_status in ["CONFIRMED", "PROCESSING"] and new_status == "CANCELLED":
                for item in order.items:
                    inventory = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
                    if inventory:
                        inventory.quantity += item.quantity

            # Update the order status
            order.status = new_status
            db.commit()
            db.refresh(order)
            return order

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update status: {str(e)}"
            )

    @classmethod
    def cancel_order(cls, db: Session, order_id: int, user_id: int) -> Order:
        """Allows a customer to cancel their own order if it is in PENDING state."""
        order = cls.get_order_by_id(db, order_id)
        if order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to cancel this order."
            )
        
        if order.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending orders can be cancelled by customers."
            )
            
        return cls.update_order_status(db, order_id, "CANCELLED")

    @staticmethod
    def get_all_orders(db: Session) -> List[Order]:
        """Fetch all orders (Admin function)."""
        return db.query(Order).all()
