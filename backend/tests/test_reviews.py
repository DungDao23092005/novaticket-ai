"""
test_reviews.py — Tests for Reviews and Sentiment analysis.
"""
from unittest.mock import patch

def test_create_review(client, db_session):
    # 1. Register and login
    client.post("/auth/register", json={"email": "rev@example.com", "username": "rev", "password": "Password123!"})
    token = client.post("/auth/login", json={"email": "rev@example.com", "password": "Password123!"}).json()["access_token"]
    
    # 2. Create Event
    from app.models.category import Category
    from app.models.event import Event
    from datetime import datetime
    
    cat = Category(name="RevCategory")
    db_session.add(cat)
    db_session.commit()
    
    event = Event(title="RevEvent", category_id=cat.id, start_date=datetime.utcnow())
    db_session.add(event)
    db_session.commit()
    
    # 3. Submit Review (mock the ML model to avoid needing trained artifacts in test)
    # We patch the SentimentService.predict method
    with patch("app.ml.sentiment_model.sentiment_model.is_loaded") as mock_is_loaded, \
        patch("app.ml.sentiment_model.sentiment_model.predict") as mock_predict:
        mock_is_loaded.return_value = True
        mock_predict.return_value = ("positive", 0.95)
        
        response = client.post(
            "/reviews/",
            json={
                "event_id": event.id,
                "rating": 5,
                "content": "This event was absolutely amazing!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["sentiment_label"] == "positive"
        
        # 4. Check GET reviews
        get_resp = client.get(f"/events/{event.id}/reviews")
        assert get_resp.status_code == 200
        assert len(get_resp.json()) == 1
        assert get_resp.json()[0]["sentiment_label"] == "positive"
