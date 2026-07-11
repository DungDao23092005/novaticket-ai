"""
test_recommendations.py — Tests for the Recommendation Engine.
"""
from unittest.mock import patch

def test_get_recommendations(client, db_session):
    # 1. Register and login
    client.post("/auth/register", json={"email": "rec@example.com", "username": "rec", "password": "Password123!"})
    token = client.post("/auth/login", json={"email": "rec@example.com", "password": "Password123!"}).json()["access_token"]
    
    # 2. Create a dummy event for recommendations to return
    from app.models.category import Category
    from app.models.event import Event
    from datetime import datetime
    
    cat = Category(name="RecCategory")
    db_session.add(cat)
    db_session.commit()
    
    event = Event(title="Mocked Event", category_id=cat.id, start_date=datetime.utcnow(), price=0.0, capacity=100, venue="V", city="C")
    db_session.add(event)
    db_session.commit()

    # 3. Add an interaction to trigger the ML profile recommender instead of Cold Start
    from app.models.interaction import UserInteraction
    from app.models.user import User
    user = db_session.query(User).filter_by(email="rec@example.com").first()
    interaction = UserInteraction(user_id=user.id, event_id=event.id, interaction_type="view")
    db_session.add(interaction)
    db_session.commit()
    
    # 4. Mock the ML recommender to avoid needing real ML artifacts
    with patch("app.ml.recommendation_model.recommender.is_loaded") as mock_loaded:
        mock_loaded.return_value = True
        with patch("app.ml.recommendation_model.recommender.recommend_for_profile") as mock_rec:
            mock_rec.return_value = [(event.id, 0.95)]
            
            response = client.get(
                "/recommendations/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Mocked Event"
