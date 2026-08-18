from app.models.user import User
from app.models.category import Category

def get_token_headers(client, db, email="test@email.com", role="customer"):
    """Helper to create a user, override role directly in DB, and get auth headers."""
    client.post(
        "/auth/register",
        json={"name": "Auth User", "email": email, "password": "password123"}
    )
    if role != "customer":
        user = db.query(User).filter(User.email == email).first()
        user.role = role
        db.commit()

    login_res = client.post(
        "/auth/login",
        data={"username": email, "password": "password123"}
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_admin_create_category(client, db):
    """Verifies admins can create categories."""
    headers = get_token_headers(client, db, email="admin@email.com", role="admin")
    
    response = client.post(
        "/categories/",
        json={"name": "Electronics"},
        headers=headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Electronics"

def test_customer_cannot_create_category(client, db):
    """Verifies customers are forbidden from creating categories."""
    headers = get_token_headers(client, db, email="customer@email.com", role="customer")
    
    response = client.post(
        "/categories/",
        json={"name": "Electronics"},
        headers=headers
    )
    assert response.status_code == 403

def test_admin_create_product(client, db):
    """Verifies admins can add products, initializing stock count to 0 in inventory."""
    admin_headers = get_token_headers(client, db, email="admin@email.com", role="admin")
    
    # 1. Create Category
    cat_res = client.post("/categories/", json={"name": "Electronics"}, headers=admin_headers)
    cat_id = cat_res.json()["id"]

    # 2. Create Product
    prod_res = client.post(
        "/products/",
        json={
            "name": "iPhone 16",
            "description": "Apple flagship",
            "price": 69999.0,
            "category_id": cat_id,
            "sku": "IP16-001"
        },
        headers=admin_headers
    )
    assert prod_res.status_code == 201
    data = prod_res.json()
    assert data["name"] == "iPhone 16"
    assert data["sku"] == "IP16-001"

    # 3. Check inventory was auto-created for the product (quantity = 0)
    inv_res = client.get("/inventory/", headers=admin_headers)
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert len(inv_data) == 1
    assert inv_data[0]["product_id"] == data["id"]
    assert inv_data[0]["quantity"] == 0

def test_product_browsing_filters(client, db):
    """Verifies filter, search, sort, and pagination functions on products."""
    admin_headers = get_token_headers(client, db, email="admin@email.com", role="admin")
    
    # Create categories
    cat1_id = client.post("/categories/", json={"name": "Electronics"}, headers=admin_headers).json()["id"]
    cat2_id = client.post("/categories/", json={"name": "Books"}, headers=admin_headers).json()["id"]

    # Create products
    client.post("/products/", headers=admin_headers, json={
        "name": "Laptop X", "description": "High performance", "price": 50000.0, "category_id": cat1_id, "sku": "LAPX"
    })
    client.post("/products/", headers=admin_headers, json={
        "name": "Phone Y", "description": "Budget cell", "price": 15000.0, "category_id": cat1_id, "sku": "PHOY"
    })
    client.post("/products/", headers=admin_headers, json={
        "name": "Python Guide", "description": "Programming book", "price": 1000.0, "category_id": cat2_id, "sku": "PYGD"
    })

    # Test Filter by Category
    res = client.get("/products/?category=Electronics")
    assert res.status_code == 200
    assert len(res.json()) == 2

    # Test Search term
    res = client.get("/products/?search=Python")
    assert len(res.json()) == 1
    assert res.json()[0]["sku"] == "PYGD"

    # Test Price Limits
    res = client.get("/products/?min_price=10000&max_price=30000")
    assert len(res.json()) == 1
    assert res.json()[0]["sku"] == "PHOY"

    # Test Sorting (price desc)
    res = client.get("/products/?sort_by=price&sort_order=desc")
    assert res.json()[0]["sku"] == "LAPX"
    assert res.json()[1]["sku"] == "PHOY"
    assert res.json()[2]["sku"] == "PYGD"

    # Test Pagination (limit 1)
    res = client.get("/products/?limit=1&page=2&sort_by=price&sort_order=desc")
    assert len(res.json()) == 1
    assert res.json()[0]["sku"] == "PHOY"
