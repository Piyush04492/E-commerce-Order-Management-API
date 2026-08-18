# E-Commerce Order Management API

🚀 **[Live Demo Link](https://e-commerce-order-management-api.onrender.com)**

A modular, production-ready, and highly educational REST API for an **E-Commerce Order Management System**. Built using **FastAPI**, **SQLAlchemy ORM**, **Pydantic V2**, and supports **SQLite** (default) and **MySQL** database drivers.

This project is specifically designed to highlight core software engineering, DBMS, and system design concepts commonly discussed in technical interviews.

---

## 🚀 Quick Start (Local Setup)

The project is pre-configured to run out-of-the-box using **SQLite** with zero configuration required.

### 1. Clone & Set Up Virtual Environment
```bash
# Create the virtual environment
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate
# Activate it (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the template to create a `.env` file:
```bash
cp .env.example .env
```
*(By default, this is configured to use SQLite: `DATABASE_URL=sqlite:///./ecommerce.db`)*

### 3. Run the Server
```bash
uvicorn app.main:app --reload
```
The server will start at **`http://127.0.0.1:8000`**.  
Open **`http://127.0.0.1:8000/docs`** in your browser to view the interactive Swagger documentation.

### 4. Run Automated Tests
```bash
pytest
```
*(Runs 17 automated tests verifying auth, shopping cart limits, FSM transitions, and transaction-safe checkouts).*

---

## 🐳 Docker Deployment (MySQL Integration)

To demonstrate containerization and running with a real MySQL server, use Docker Compose.

```bash
# Build the containers and launch services
docker-compose up --build
```
This orchestrates:
1. A **MySQL 8.4** database container with persistent volumes.
2. A **FastAPI** web application container connected to the database.
3. Health check configurations: The web container waits for MySQL to be healthy before booting.

---

## 📂 Project Architecture

The directory layout implements a clean separation of concerns:

```
app/
├── main.py                  # App entrypoint, middleware, and route registration
├── config.py                # Environment variables parser via Pydantic Settings
├── database/
│   ├── connection.py        # SQLAlchemy engine, session maker, and get_db dependency
│   └── base.py              # Declarative base class for ORM models
├── models/                  # SQLAlchemy Database Models (SQL Schema definitions)
├── schemas/                 # Pydantic Schemas (Request/Response validators & DTOs)
├── routes/                  # API Controllers (Auth, Cart, Orders, Products, Analytics)
├── services/                # Encapsulated Business Logic layer (Checkout, Payments, Stock)
└── utils/                   # Shared helpers (direct bcrypt hashing, FSM validators)
```

---

## 🛠️ Step-by-Step API Walkthrough Scenarios

Open the Swagger Docs (`/docs`) and try this sequence to test the entire lifecycle:

### Scenario A: Product Setup (Admin Role)
1. **Register Admin**: Call `POST /auth/register`. After registration, manually toggle their role to `"admin"` in the database (or run the tests where this is handled).
2. **Login Admin**: Call `POST /auth/login` using the Swagger "Authorize" button or endpoint. This returns a JWT token.
3. **Create Category**: Call `POST /categories` to add a new category (e.g. `Electronics`).
4. **Create Products**: Call `POST /products` to add products (e.g. `iPhone 16` with SKU `IP16` and `Laptop` with SKU `LAP1`).
5. **Add Stock**: Call `PUT /inventory/{product_id}` to set quantities (e.g. set iPhone stock to `10` and reorder level to `3`).

### Scenario B: Customer Shopping Flow
1. **Register Customer**: Call `POST /auth/register` (e.g., Piyush).
2. **Login Customer**: Call `POST /auth/login` to obtain the customer JWT.
3. **Browse Catalog**: Call `GET /products?category=Electronics&min_price=10000` to verify search, filtering, and sorting parameters.
4. **Add to Cart**: Call `POST /cart/items` with a quantity of `2` iPhones.
5. **Checkout**: Call `POST /orders/checkout` with a shipping address. This returns a pending order.
6. **Payment**: Call `POST /payments/` supplying the `order_id` with `simulate_success` set to `True`. The order status moves to `CONFIRMED` and inventory is settled.
7. **Track Orders**: Call `GET /orders/` to view your complete order history.
