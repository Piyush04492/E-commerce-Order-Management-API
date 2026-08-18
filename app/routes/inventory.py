from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.schemas.inventory import InventoryResponse, InventoryUpdate, LowStockAlert
from app.services.inventory_service import InventoryService
from app.models.user import User
from app.routes.deps import get_current_admin

router = APIRouter(prefix="/inventory", tags=["Inventory Management"])

@router.get("/", response_model=List[InventoryResponse])
def get_inventory(
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    """
    View complete system inventory ledger.
    Restricted to Admins.
    """
    return InventoryService.get_all_inventory(db)

@router.put("/{product_id}", response_model=InventoryResponse)
def update_inventory(
    product_id: int,
    update_data: InventoryUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Modifies physical count, reserved quantity, or low stock reorder thresholds for a product.
    Restricted to Admins.
    """
    return InventoryService.update_inventory_by_product(db, product_id, update_data)

@router.get("/alerts", response_model=List[LowStockAlert])
def get_low_stock_alerts(
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    """
    View a list of products whose stock is below their reorder_level.
    Restricted to Admins.
    """
    return InventoryService.get_low_stock_alerts(db)
