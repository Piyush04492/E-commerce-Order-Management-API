def test_register_customer(client):
    """Verifies that customers can register successfully."""
    response = client.post(
        "/auth/register",
        json={"name": "Piyush", "email": "piyush@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Piyush"
    assert data["email"] == "piyush@example.com"
    assert data["role"] == "customer"
    assert "id" in data

def test_register_duplicate_email(client):
    """Verifies that duplicate registrations fail with 400 Bad Request."""
    client.post(
        "/auth/register",
        json={"name": "Piyush", "email": "piyush@example.com", "password": "password123"}
    )
    response = client.post(
        "/auth/register",
        json={"name": "Piyush Dup", "email": "piyush@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "A user with this email already exists."

def test_login_success(client):
    """Verifies successful login returns JWT."""
    client.post(
        "/auth/register",
        json={"name": "Piyush", "email": "piyush@example.com", "password": "password123"}
    )
    response = client.post(
        "/auth/login",
        data={"username": "piyush@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client):
    """Verifies login fails with incorrect password."""
    client.post(
        "/auth/register",
        json={"name": "Piyush", "email": "piyush@example.com", "password": "password123"}
    )
    response = client.post(
        "/auth/login",
        data={"username": "piyush@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_get_current_profile(client):
    """Verifies that profile data can be fetched using JWT."""
    client.post(
        "/auth/register",
        json={"name": "Piyush", "email": "piyush@example.com", "password": "password123"}
    )
    login_res = client.post(
        "/auth/login",
        data={"username": "piyush@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Piyush"
    assert data["email"] == "piyush@example.com"
