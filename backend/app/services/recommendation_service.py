"""
services/recommendation_service.py — Business logic for personalized event recommendations.

Orchestrates:
    1. InteractionRepository  — Get user's past behaviors
    2. EventRepository        — Fetch event details and handle cold-start
    3. RecommendationModel    — ML inference for content-based profile matching

Strategy:
    - If user has interactions (views, clicks, reviews):
        Build a TF-IDF profile from their past events and recommend similar ones.
    - If user is new (Cold Start):
        Fallback to returning the newest/most popular active events.
"""

import logging
from app.ml.recommendation_model import recommender
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.repositories.interaction_repository import InteractionRepository

logger = logging.getLogger(__name__)


class RecommendationService:
    def __init__(self, db) -> None:
        self.db = db
        self.event_repo = EventRepository(db)
        self.interaction_repo = InteractionRepository(db)

    def get_recommendations_for_user(self, user_id: int, top_k: int = 5) -> list[Event]:
        """
        Get personalized event recommendations for a specific user.
        
        Args:
            user_id: The ID of the authenticated user
            top_k: Number of recommendations to return
            
        Returns:
            List of Event ORM objects (ordered by recommendation score/relevance)
        """
        # 1. Fetch user's historical interactions
        interactions = self.interaction_repo.get_by_user(user_id)
        
        # 2. Extract unique event IDs the user has interacted with
        # (Using a set to avoid duplicates, then list for the ML model)
        past_event_ids = list({interaction.event_id for interaction in interactions})
        
        recommended_events = []
        
        # 3. If model is loaded and user has history, use Content-Based Profile Recommender
        if recommender.is_loaded() and len(past_event_ids) > 0:
            logger.info(f"User {user_id} has {len(past_event_ids)} past interactions. Generating profile-based recommendations.")
            
            # Returns list of tuples: (event_id, score)
            rec_results = recommender.recommend_for_profile(past_event_ids, top_k=top_k)
            rec_event_ids = [eid for eid, score in rec_results]
            
            if rec_event_ids:
                # Fetch full Event objects from DB
                # Note: We need to preserve the order returned by the ML model
                events_dict = {
                    e.id: e for e in self.db.query(Event).filter(Event.id.in_(rec_event_ids)).all()
                }
                
                for eid in rec_event_ids:
                    if eid in events_dict:
                        recommended_events.append(events_dict[eid])

        # 4. Fallback (Cold Start OR ML model failed/not loaded)
        # If we couldn't get enough recommendations, fill the rest with newest events
        if len(recommended_events) < top_k:
            logger.info(f"Falling back to newest events for user {user_id} (Cold Start or insufficient ML results).")
            
            # Get IDs we already recommended or user already saw to exclude them
            exclude_ids = set(past_event_ids) | {e.id for e in recommended_events}
            
            # Fetch newest active events
            newest_events = self.event_repo.get_all(limit=top_k * 2) # Fetch extra to account for exclusions
            
            for event in newest_events.items:
                if event.id not in exclude_ids:
                    recommended_events.append(event)
                if len(recommended_events) >= top_k:
                    break
                    
        return recommended_events[:top_k]

    def get_similar_events(self, event_id: int, top_k: int = 4) -> list[Event]:
        """
        Get events similar to a specific event (e.g., for 'You might also like' section on detail page).
        """
        if not recommender.is_loaded():
            return []
            
        rec_results = recommender.get_similar_events(event_id, top_k=top_k)
        rec_event_ids = [eid for eid, score in rec_results]
        
        if not rec_event_ids:
            return []
            
        # Fetch from DB and preserve ML order
        events_dict = {
            e.id: e for e in self.db.query(Event).filter(Event.id.in_(rec_event_ids)).all()
        }
        
        return [events_dict[eid] for eid in rec_event_ids if eid in events_dict]
