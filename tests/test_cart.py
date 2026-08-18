from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.inventory import Inventory

def get_auth_client(client, db, email="customer@email.com"):
    """Seeds a customer user and logs them in."""
    client.post(
        "/auth/register",
        json={"name": "Piyush", "email": email, "password": "password123"}
    )
    login_res = client.post(
        "/auth/login",
        data={"username": email, "password": "password123"}
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def seed_product_with_stock(db, name="iPhone", price=70000.0, sku="IPHONE", quantity=10):
    """Directly seeds database with a category, product, and inventory."""
    cat = Category(name="Electronics")
    db.add(cat)
    db.commit()

    prod = Product(name=name, description="Test phone", price=price, category_id=cat.id, sku=sku)
    db.add(prod)
    db.commit()

    inv = Inventory(product_id=prod.id, quantity=quantity, reserved_quantity=0, reorder_level=2)
    db.add(inv)
    db.commit()
    return prod, inv

def test_add_item_to_cart(client, db):
    """Verifies adding a product to cart and stock checking."""
    headers = get_auth_client(client, db)
    prod, inv = seed_product_with_stock(db, quantity=5)

    # 1. Successful Add
    res = client.post("/cart/items", json={"product_id": prod.id, "quantity": 3}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == prod.id
    assert data["items"][0]["quantity"] == 3

    # 2. Exceeding Inventory Add (already has 3 in cart, adding 3 more = 6 > 5)
    res_exceed = client.post("/cart/items", json={"product_id": prod.id, "quantity": 3}, headers=headers)
    assert res_exceed.status_code == 400
    assert "Insufficient" in res_exceed.json()["detail"]

def test_update_cart_quantity(client, db):
    """Verifies updating cart item count with stock check."""
    headers = get_auth_client(client, db)
    prod, inv = seed_product_with_stock(db, quantity=5)

    # Add item
    client.post("/cart/items", json={"product_id": prod.id, "quantity": 1}, headers=headers)
    cart = client.get("/cart/", headers=headers).json()
    item_id = cart["items"][0]["id"]

    # 1. Update quantity successfully
    res = client.put(f"/cart/items/{item_id}", json={"quantity": 4}, headers=headers)
    assert res.status_code == 200
    assert res.json()["items"][0]["quantity"] == 4

    # 2. Exceed stock update
    res_exceed = client.put(f"/cart/items/{item_id}", json={"quantity": 10}, headers=headers)
    assert res_exceed.status_code == 400

def test_delete_cart_item(client, db):
    """Verifies deleting item from cart."""
    headers = get_auth_client(client, db)
    prod, inv = seed_product_with_stock(db, quantity=5)

    # Add item
    client.post("/cart/items", json={"product_id": prod.id, "quantity": 1}, headers=headers)
    cart = client.get("/cart/", headers=headers).json()
    item_id = cart["items"][0]["id"]

    # Delete item
    res = client.delete(f"/cart/items/{item_id}", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 0
