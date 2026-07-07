"""
app/ml/recommendation_model.py — Content-Based Recommendation Inference.

Loads trained TF-IDF artifacts once at module import time (singleton pattern).
Provides methods to compute similarities and recommend events.

Artifact paths (relative to backend/):
    models/tfidf_content.joblib
    models/event_matrix.joblib
    models/cf_matrix.joblib

Usage:
    from app.ml.recommendation_model import recommender

    if recommender.is_loaded():
        # Get similar events to event ID 1
        similar = recommender.get_similar_events(event_id=1, top_k=5)
        
        # Build user profile from past events and recommend
        recs = recommender.recommend_for_profile(past_event_ids=[1, 5], top_k=5)
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Paths relative to backend/ directory
_BACKEND_DIR = Path(__file__).parent.parent.parent
_MODELS_DIR = _BACKEND_DIR / "models"
_TFIDF_PATH = _MODELS_DIR / "tfidf_content.joblib"
_MATRIX_PATH = _MODELS_DIR / "event_matrix.joblib"
_CF_MATRIX_PATH = _MODELS_DIR / "cf_matrix.joblib"


class RecommendationModel:
    """
    Singleton wrapper around the Content-Based Recommender.
    Loads TF-IDF vectorizer and event matrix on startup.
    Handles missing artifacts gracefully.
    """

    def __init__(self) -> None:
        self._vectorizer = None
        self._event_ids = None      # 1D numpy array of event IDs (CBF)
        self._tfidf_matrix = None   # Sparse matrix (CBF)
        
        self._event_ids_cf = None   # 1D numpy array of event IDs (CF)
        self._cf_matrix = None      # CF features matrix
        
        self._loaded = False
        self._load()

    def _load(self) -> None:
        try:
            import joblib
            import numpy as np

            if not _TFIDF_PATH.exists() or not _MATRIX_PATH.exists():
                logger.warning(
                    "Recommender artifacts not found. "
                    "Run: python training/train_recommender.py"
                )
                return

            self._vectorizer = joblib.load(_TFIDF_PATH)
            matrix_data = joblib.load(_MATRIX_PATH)
            
            self._event_ids = matrix_data["event_ids"]
            self._tfidf_matrix = matrix_data["tfidf_matrix"]
            
            # Load CF matrix if exists
            if _CF_MATRIX_PATH.exists():
                cf_data = joblib.load(_CF_MATRIX_PATH)
                self._event_ids_cf = cf_data["event_ids"]
                self._cf_matrix = cf_data["cf_matrix"]
                logger.info(f"CF matrix loaded ({len(self._event_ids_cf)} events).")
                
            self._loaded = True
            
            logger.info(f"CBF Recommender loaded successfully ({len(self._event_ids)} events).")

        except Exception as exc:
            logger.error("Failed to load recommender model: %s", exc)
            self._loaded = False

    def is_loaded(self) -> bool:
        """Return True if artifacts are loaded and ready."""
        return self._loaded

    def get_similar_events(self, event_id: int, top_k: int = 5) -> list[tuple[int, float]]:
        """
        Find most similar events to a given event using Cosine Similarity.
        
        Args:
            event_id: The target event ID
            top_k: Number of recommendations to return
            
        Returns:
            List of tuples (event_id, similarity_score)
        """
        if not self._loaded:
            return []

        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        # Find row index of the target event
        indices = np.where(self._event_ids == event_id)[0]
        if len(indices) == 0:
            return [] # Event not in our matrix (maybe newly created)
        
        idx = indices[0]
        event_vector = self._tfidf_matrix[idx]
        
        # Compute cosine similarity between this event and all others
        sim_scores = cosine_similarity(event_vector, self._tfidf_matrix).flatten()
        
        # Sort indices by score (descending)
        sorted_indices = sim_scores.argsort()[::-1]
        
        results = []
        for i in sorted_indices:
            # Skip the target event itself
            if self._event_ids[i] == event_id:
                continue
                
            score = float(sim_scores[i])
            if score > 0.0: # Only return items with some similarity
                results.append((int(self._event_ids[i]), round(score, 4)))
                
            if len(results) >= top_k:
                break
                
        return results

    def recommend_for_profile(self, past_event_ids: list[int], top_k: int = 5) -> list[tuple[int, float]]:
        """
        Builds a user profile by averaging TF-IDF vectors of their past events,
        then finds similar events.
        
        Args:
            past_event_ids: List of event IDs the user has interacted with
            top_k: Number of recommendations to return
            
        Returns:
            List of tuples (event_id, similarity_score)
        """
        if not self._loaded or not past_event_ids:
            return []

        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Find row indices for past events
        indices = []
        for eid in past_event_ids:
            idx_match = np.where(self._event_ids == eid)[0]
            if len(idx_match) > 0:
                indices.append(idx_match[0])
                
        if not indices:
            return [] # None of the past events are in our matrix
            
        # Create user profile by averaging their past event vectors
        # Using sparse matrix operations
        user_profile = self._tfidf_matrix[indices].mean(axis=0)
        user_profile = np.asarray(user_profile) # Convert np.matrix to np.array to fix sklearn TypeError
        
        # 1. Content-Based Scores
        cbf_scores = cosine_similarity(user_profile, self._tfidf_matrix).flatten()
        
        # 2. Collaborative Filtering Scores (if available)
        cf_scores = np.zeros_like(cbf_scores)
        if self._cf_matrix is not None:
            # Build user profile for CF
            cf_indices = []
            for eid in past_event_ids:
                idx_match = np.where(self._event_ids_cf == eid)[0]
                if len(idx_match) > 0:
                    cf_indices.append(idx_match[0])
            
            if cf_indices:
                user_cf_profile = self._cf_matrix[cf_indices].mean(axis=0).reshape(1, -1)
                cf_sim = cosine_similarity(user_cf_profile, self._cf_matrix).flatten()
                
                # Map CF scores back to the main event IDs index space
                for idx_cf, cf_eid in enumerate(self._event_ids_cf):
                    idx_cbf_match = np.where(self._event_ids == cf_eid)[0]
                    if len(idx_cbf_match) > 0:
                        cf_scores[idx_cbf_match[0]] = cf_sim[idx_cf]
                        
        # 3. Hybrid scoring (Blend CBF and CF)
        # 70% Content-based, 30% CF (since CF data might be sparse initially)
        weight_cbf = 0.7 if self._cf_matrix is not None else 1.0
        weight_cf = 0.3 if self._cf_matrix is not None else 0.0
        
        hybrid_scores = (cbf_scores * weight_cbf) + (cf_scores * weight_cf)
        
        # Sort indices
        sorted_indices = hybrid_scores.argsort()[::-1]
        
        results = []
        for i in sorted_indices:
            # Skip events the user has already interacted with
            if self._event_ids[i] in past_event_ids:
                continue
                
            score = float(hybrid_scores[i])
            if score > 0.0:
                results.append((int(self._event_ids[i]), round(score, 4)))
                
            if len(results) >= top_k:
                break
                
        return results


# Singleton instance
recommender = RecommendationModel()
