from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order

def seed_test_data(db):
    """Utility to seed user, category, product, and inventory in test db."""
    # Seed Customer & Admin
    cust = User(name="Customer", email="customer@example.com", password_hash="hashed", role="customer")
    admin = User(name="Admin", email="admin@example.com", password_hash="hashed", role="admin")
    db.add_all([cust, admin])
    db.commit()

    cat = Category(name="Electronics")
    db.add(cat)
    db.commit()

    p1 = Product(name="iPhone 16", description="Apple", price=70000.0, category_id=cat.id, sku="IP16")
    p2 = Product(name="Laptop Y", description="Dell", price=50000.0, category_id=cat.id, sku="D50")
    db.add_all([p1, p2])
    db.commit()

    inv1 = Inventory(product_id=p1.id, quantity=10, reserved_quantity=0, reorder_level=2)
    inv2 = Inventory(product_id=p2.id, quantity=5, reserved_quantity=0, reorder_level=1)
    db.add_all([inv1, inv2])
    db.commit()

    return cust, admin, p1, p2, inv1, inv2

def get_auth_headers(client, email):
    login_res = client.post(
        "/auth/login",
        data={"username": email, "password": "password123"}
    )
    # If the user doesn't exist, we must register first.
    # To keep it simple, we register through client, then override passwords if needed.
    # Or register directly with the password "password123".
    # Let's register through client instead to ensure valid pass hashes!
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}

def setup_users_and_get_headers(client, db):
    """Helper that registers a customer and an admin with correct password hashing."""
    client.post("/auth/register", json={"name": "Customer", "email": "customer@example.com", "password": "password123"})
    client.post("/auth/register", json={"name": "Admin", "email": "admin@example.com", "password": "password123"})
    
    # Make admin an admin in the database
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    admin.role = "admin"
    db.commit()

    # Seed products
    cat = Category(name="Electronics")
    db.add(cat)
    db.commit()

    p1 = Product(name="iPhone 16", description="Apple", price=70000.0, category_id=cat.id, sku="IP16")
    db.add(p1)
    db.commit()

    inv1 = Inventory(product_id=p1.id, quantity=10, reserved_quantity=0, reorder_level=2)
    db.add(inv1)
    db.commit()

    cust_headers = get_auth_headers(client, "customer@example.com")
    admin_headers = get_auth_headers(client, "admin@example.com")
    
    return cust_headers, admin_headers, p1, inv1

def test_checkout_and_stock_reservation(client, db):
    """Verifies that checkout reserves stock, freezes price, and clears cart."""
    c_headers, a_headers, prod, inv = setup_users_and_get_headers(client, db)

    # 1. Add item to cart
    client.post("/cart/items", json={"product_id": prod.id, "quantity": 3}, headers=c_headers)

    # 2. Checkout
    res = client.post("/orders/checkout", json={"shipping_address": "123 Main St"}, headers=c_headers)
    assert res.status_code == 201
    order_data = res.json()
    assert order_data["status"] == "PENDING"
    assert order_data["total_amount"] == 210000.0  # 3 * 70000
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["unit_price"] == 70000.0

    # 3. Check inventory state: reserved_quantity should be 3, quantity still 10
    db.refresh(inv)
    assert inv.reserved_quantity == 3
    assert inv.quantity == 10
    assert inv.available_quantity == 7

    # 4. Check cart is cleared
    cart_res = client.get("/cart/", headers=c_headers)
    assert len(cart_res.json()["items"]) == 0

def test_payment_success_settles_stock(client, db):
    """Verifies that a successful payment changes status to CONFIRMED and settles inventory."""
    c_headers, a_headers, prod, inv = setup_users_and_get_headers(client, db)
    client.post("/cart/items", json={"product_id": prod.id, "quantity": 3}, headers=c_headers)
    order_id = client.post("/orders/checkout", json={"shipping_address": "123 Main St"}, headers=c_headers).json()["id"]

    # Trigger Payment Success simulation
    pay_res = client.post(
        f"/payments/?order_id={order_id}", 
        json={"payment_method": "credit_card", "simulate_success": True}, 
        headers=c_headers
    )
    assert pay_res.status_code == 201
    assert pay_res.json()["status"] == "SUCCESS"

    # Confirm Order is now CONFIRMED
    order_res = client.get(f"/orders/{order_id}", headers=c_headers)
    assert order_res.json()["status"] == "CONFIRMED"

    # Confirm Stock was settled: quantity = 7, reserved_quantity = 0
    db.refresh(inv)
    assert inv.quantity == 7
    assert inv.reserved_quantity == 0

def test_payment_failure_releases_stock(client, db):
    """Verifies that failed payment changes status to CANCELLED and releases reservation."""
    c_headers, a_headers, prod, inv = setup_users_and_get_headers(client, db)
    client.post("/cart/items", json={"product_id": prod.id, "quantity": 3}, headers=c_headers)
    order_id = client.post("/orders/checkout", json={"shipping_address": "123 Main St"}, headers=c_headers).json()["id"]

    # Trigger Payment Failure simulation
    pay_res = client.post(
        f"/payments/?order_id={order_id}", 
        json={"payment_method": "credit_card", "simulate_success": False}, 
        headers=c_headers
    )
    assert pay_res.status_code == 201
    assert pay_res.json()["status"] == "FAILED"

    # Confirm Order is now CANCELLED
    order_res = client.get(f"/orders/{order_id}", headers=c_headers)
    assert order_res.json()["status"] == "CANCELLED"

    # Confirm Stock reservation was released: quantity = 10, reserved = 0
    db.refresh(inv)
    assert inv.quantity == 10
    assert inv.reserved_quantity == 0

def test_restock_on_confirmed_order_cancellation(client, db):
    """Verifies that cancelling an already CONFIRMED order returns physical stock to inventory."""
    c_headers, a_headers, prod, inv = setup_users_and_get_headers(client, db)
    client.post("/cart/items", json={"product_id": prod.id, "quantity": 3}, headers=c_headers)
    order_id = client.post("/orders/checkout", json={"shipping_address": "123 Main St"}, headers=c_headers).json()["id"]

    # Pay successfully -> CONFIRMED (stock goes down to 7)
    client.post(f"/payments/?order_id={order_id}", json={"payment_method": "credit_card", "simulate_success": True}, headers=c_headers)
    db.refresh(inv)
    assert inv.quantity == 7

    # Cancel confirmed order (by Admin)
    cancel_res = client.put(f"/orders/{order_id}/status", json={"status": "CANCELLED"}, headers=a_headers)
    assert cancel_res.status_code == 200

    # Physical stock should return to 10
    db.refresh(inv)
    assert inv.quantity == 10
    assert inv.reserved_quantity == 0

def test_invalid_status_transition_fails(client, db):
    """Verifies FSM: invalid transitions (e.g. DELIVERED -> PENDING) fail with 400."""
    c_headers, a_headers, prod, inv = setup_users_and_get_headers(client, db)
    client.post("/cart/items", json={"product_id": prod.id, "quantity": 1}, headers=c_headers)
    order_id = client.post("/orders/checkout", json={"shipping_address": "123 Main St"}, headers=c_headers).json()["id"]

    # Try transitioning PENDING -> DELIVERED (invalid, must be shipped first)
    res = client.put(f"/orders/{order_id}/status", json={"status": "DELIVERED"}, headers=a_headers)
    assert res.status_code == 400
    assert "Invalid transition" in res.json()["detail"]
