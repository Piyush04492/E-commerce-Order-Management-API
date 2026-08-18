from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.inventory import InventoryUpdate, LowStockAlert

class InventoryService:
    """
    Manages inventory stock levels, reorder parameters, and low-stock indicators.
    """

    @staticmethod
    def get_all_inventory(db: Session) -> List[Inventory]:
        """Fetch all inventory records."""
        return db.query(Inventory).all()

    @staticmethod
    def update_inventory_by_product(db: Session, product_id: int, update_data: InventoryUpdate) -> Inventory:
        """Updates stock count or reorder levels for a specific product."""
        inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
        if not inventory:
            # If no inventory record exists yet (e.g. legacy product), create one
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="Product not found."
                )
            inventory = Inventory(product_id=product_id)
            db.add(inventory)
            db.commit()
            db.refresh(inventory)

        # Update fields dynamically
        if update_data.quantity is not None:
            inventory.quantity = update_data.quantity
        if update_data.reserved_quantity is not None:
            # Simple safety checks
            if update_data.reserved_quantity > inventory.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reserved quantity cannot exceed total physical quantity."
                )
            inventory.reserved_quantity = update_data.reserved_quantity
        if update_data.reorder_level is not None:
            inventory.reorder_level = update_data.reorder_level

        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def get_low_stock_alerts(db: Session) -> List[LowStockAlert]:
        """
        Returns a list of products where current physical stock 
        falls below the specified reorder level threshold.
        """
        results = db.query(Inventory, Product).join(
            Product, Inventory.product_id == Product.id
        ).filter(
            Inventory.quantity < Inventory.reorder_level
        ).all()

        alerts = []
        for inv, prod in results:
            alerts.append(LowStockAlert(
                product_id=prod.id,
                product_name=prod.name,
                sku=prod.sku,
                quantity=inv.quantity,
                reorder_level=inv.reorder_level
            ))
        return alerts
