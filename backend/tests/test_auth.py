"""
test_auth.py — Tests for the Auth router and service.
"""

def test_register_user_success(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "Password123!",
            "full_name": "Test User"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["username"] == "testuser"
    assert "hashed_password" not in data
    assert "id" in data

def test_register_user_duplicate_email(client):
    # Register first time
    client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "Password123!"
        },
    )
    
    # Register second time with same email
    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "Password123!"
        },
    )
    assert response.status_code == 409
    assert "Email already registered" in response.json()["detail"]

def test_login_success(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "email": "loginuser@example.com",
            "username": "loginuser",
            "password": "StrongPassword!"
        },
    )
    
    # Login
    response = client.post(
        "/auth/login",
        json={
            "email": "loginuser@example.com",
            "password": "StrongPassword!"
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrongpass@example.com",
            "username": "wrongpass",
            "password": "CorrectPassword!"
        },
    )
    
    response = client.post(
        "/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPassword!"
        },
    )
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_get_me_success(client):
    client.post(
        "/auth/register",
        json={
            "email": "me@example.com",
            "username": "me_user",
            "password": "Password123!"
        },
    )
    
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "me@example.com",
            "password": "Password123!"
        },
    )
    token = login_resp.json()["access_token"]
    
    # Get profile using JWT
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
