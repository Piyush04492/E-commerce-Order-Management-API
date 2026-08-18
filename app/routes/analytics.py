from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.connection import get_db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.routes.deps import get_current_admin

router = APIRouter(prefix="/analytics", tags=["Admin Analytics"])

@router.get("/")
def get_dashboard_analytics(
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    """
    Retrieves system KPIs for the admin dashboard.
    Demonstrates SQL JOINs, GROUP BY, aggregations (SUM, COUNT), and sorting via SQLAlchemy.
    Calculates:
    - Total customers.
    - Cumulative revenue of active/paid orders.
    - Breakdown of order statuses.
    - Top 5 selling products by quantity.
    Restricted to Admins.
    """
    # 1. Total Customers Count
    total_customers = db.query(func.count(User.id)).filter(User.role == "customer").scalar() or 0

    # 2. Cumulative Revenue from paid/confirmed orders
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status.in_(["CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED"])
    ).scalar() or 0.0

    # 3. Order volume breakdown by status
    status_group = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    orders_breakdown = {status: count for status, count in status_group}

    # 4. Top 5 Selling Products (joined with OrderItem and confirmed Orders)
    top_products_query = db.query(
        Product.id,
        Product.name,
        Product.sku,
        func.sum(OrderItem.quantity).label("total_sold")
    ).join(OrderItem, Product.id == OrderItem.product_id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(Order.status.in_(["CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED"]))\
     .group_by(Product.id, Product.name, Product.sku)\
     .order_by(desc("total_sold"))\
     .limit(5).all()

    top_products = [
        {
            "product_id": pid,
            "product_name": name,
            "sku": sku,
            "total_sold": int(sold)
        }
        for pid, name, sku, sold in top_products_query
    ]

    return {
        "total_customers": total_customers,
        "total_revenue": float(total_revenue),
        "orders_breakdown": orders_breakdown,
        "top_products": top_products
    }
