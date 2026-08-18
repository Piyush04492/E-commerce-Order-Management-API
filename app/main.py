from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import engine
from app.database.base import Base

# Import all models so SQLAlchemy is aware of them before creating tables.
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.payment import Payment

# Import route controllers
from app.routes import auth, users, products, categories, cart, orders, payments, inventory, analytics

# Initialize database schema (runs CREATE TABLE query if tables do not exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-Commerce Order Management API",
    description=(
        "A modular REST API representing an E-Commerce Order Management System. "
        "Built using FastAPI, SQLAlchemy ORM, and SQLite/MySQL. "
        "Designed to showcase software engineering concepts (FSM order transitions, "
        "atomic transactions, token authorization) for technical interviews."
    ),
    version="1.0.0"
)

# Enable CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include sub-routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(inventory.router)
app.include_router(analytics.router)

@app.get("/", tags=["Root"])
def read_root():
    """Welcome page with redirection advice to OpenAPI docs."""
    return {
        "message": "Welcome to the E-Commerce Order Management API!",
        "documentation": "/docs"
    }
