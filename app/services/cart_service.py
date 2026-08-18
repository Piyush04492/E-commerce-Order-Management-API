from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.inventory import Inventory
from app.schemas.cart import CartItemAdd

class CartService:
    """
    Manages customer shopping cart logic.
    Ensures that items added do not exceed current available stock.
    """

    @staticmethod
    def get_or_create_cart(db: Session, user_id: int) -> Cart:
        """Fetch the user's cart, or create it if it doesn't exist."""
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        return cart

    @classmethod
    def add_item_to_cart(cls, db: Session, user_id: int, item_data: CartItemAdd) -> Cart:
        """Adds a product to the cart or increments its quantity, validating stock first."""
        cart = cls.get_or_create_cart(db, user_id)
        
        # Verify product exists
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Product not found"
            )
        
        # Verify inventory exists
        inventory = db.query(Inventory).filter(Inventory.product_id == item_data.product_id).first()
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Product inventory record not found."
            )
            
        # Check if item is already in the cart
        cart_item = db.query(CartItem).filter(
            CartItem.cart_id == cart.id, 
            CartItem.product_id == item_data.product_id
        ).first()
        
        new_quantity = item_data.quantity
        if cart_item:
            new_quantity += cart_item.quantity
            
        # Validate available stock: quantity - reserved_quantity
        if inventory.available_quantity < new_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient inventory. Only {inventory.available_quantity} items available."
            )
            
        if cart_item:
            cart_item.quantity = new_quantity
        else:
            cart_item = CartItem(
                cart_id=cart.id, 
                product_id=item_data.product_id, 
                quantity=item_data.quantity
            )
            db.add(cart_item)
            
        db.commit()
        db.refresh(cart)
        return cart

    @classmethod
    def update_cart_item(cls, db: Session, user_id: int, cart_item_id: int, quantity: int) -> Cart:
        """Modifies the quantity of a cart item, validating stock."""
        cart = cls.get_or_create_cart(db, user_id)
        cart_item = db.query(CartItem).filter(
            CartItem.id == cart_item_id, 
            CartItem.cart_id == cart.id
        ).first()
        
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Cart item not found."
            )
            
        inventory = db.query(Inventory).filter(Inventory.product_id == cart_item.product_id).first()
        if not inventory or inventory.available_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient inventory. Only {inventory.available_quantity if inventory else 0} items available."
            )
            
        cart_item.quantity = quantity
        db.commit()
        db.refresh(cart)
        return cart

    @classmethod
    def delete_cart_item(cls, db: Session, user_id: int, cart_item_id: int) -> Cart:
        """Removes an item from the cart."""
        cart = cls.get_or_create_cart(db, user_id)
        cart_item = db.query(CartItem).filter(
            CartItem.id == cart_item_id, 
            CartItem.cart_id == cart.id
        ).first()
        
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Cart item not found."
            )
            
        db.delete(cart_item)
        db.commit()
        db.refresh(cart)
        return cart

    @staticmethod
    def clear_cart(db: Session, cart_id: int):
        """Helper to clear all items in a cart after checkout."""
        db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
        db.commit()
