"""
test_events.py — Tests for the Events and Categories endpoints.
"""
import pytest

def test_create_category(client):
    # Register user and get token
    client.post("/auth/register", json={"email": "admin@example.com", "username": "admin", "password": "StrongPass123!"})
    token = client.post("/auth/login", json={"email": "admin@example.com", "password": "StrongPass123!"}).json()["access_token"]

    # Create category
    response = client.post(
        "/categories",
        json={"name": "New Category", "description": "A test category"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Category"
    assert data["description"] == "A test category"

    # Duplicate name should return 409
    response = client.post(
        "/categories",
        json={"name": "New Category"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 409

    # Unauthenticated should return 401
    response = client.post("/categories", json={"name": "No Auth Category"})
    assert response.status_code == 401

def test_get_categories(client, db_session):
    # Insert a dummy category directly into DB
    from app.models.category import Category
    cat = Category(name="Test Concerts", description="Live music")
    db_session.add(cat)
    db_session.commit()
    
    response = client.get("/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(c["name"] == "Test Concerts" for c in data)

def test_get_events(client, db_session):
    # Insert dummy event
    from app.models.category import Category
    from app.models.event import Event
    from datetime import datetime, timedelta
    
    cat = Category(name="Tech", description="Tech events")
    db_session.add(cat)
    db_session.commit()
    
    event = Event(
        title="AI Summit 2026",
        description="Future of AI",
        category_id=cat.id,
        venue="Convention Center",
        city="Hanoi",
        start_date=datetime.utcnow() + timedelta(days=10),
        price=100.0,
        capacity=500
    )
    db_session.add(event)
    db_session.commit()
    
    response = client.get("/events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    
    # Test getting specific event
    event_id = data["items"][0]["id"]
    detail_resp = client.get(f"/events/{event_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["title"] == "AI Summit 2026"
