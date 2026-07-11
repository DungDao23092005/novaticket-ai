"""
training/train_recommender.py — Offline Recommendation Model Training Pipeline.

Usage (from backend/ directory, with venv activated):
    python training/train_recommender.py

What this does:
    1. Loads all active events from SQL Server DB.
    2. Builds a rich text document for each event using title, category, tags, and description.
    3. Fits a TF-IDF vectorizer on these documents to capture semantic meaning.
    4. Saves the vectorizer and the transformed TF-IDF matrix as artifacts.

Output artifacts:
    models/tfidf_content.joblib   — Fitted TF-IDF vectorizer (Content-Based)
    models/event_matrix.joblib    — TF-IDF event matrix (Content-Based)
    models/cf_matrix.joblib       — Item-Item Collaborative Filtering matrix
    
These artifacts are loaded at startup by the inference service.
"""

import sys
from pathlib import Path
import logging

# Add backend/ to sys.path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
MODELS_DIR = BACKEND_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

TFIDF_PATH = MODELS_DIR / "tfidf_content.joblib"
EVENT_MATRIX_PATH = MODELS_DIR / "event_matrix.joblib"
CF_MATRIX_PATH = MODELS_DIR / "cf_matrix.joblib"


# ----------------------------------------------------------------------
# Data loading & Feature Engineering
# ----------------------------------------------------------------------
def load_and_prepare_events() -> tuple[list[int], list[str]]:
    """
    Load active events from DB and create a content document for each.
    Returns:
        event_ids: List of integer event IDs
        documents: List of text strings combining title, category, tags, desc
    """
    from app.database.connection import SessionLocal
    from app.models.event import Event
    from app.models.category import Category

    db = SessionLocal()
    event_ids = []
    documents = []
    
    try:
        # Load active events, join with category for richer text features
        events = db.query(Event, Category).outerjoin(Category, Event.category_id == Category.id).filter(Event.is_active == True).all()
        
        for event, category in events:
            # Construct a rich text document for content-based filtering
            # We weight title and category higher by repeating them
            title = event.title or ""
            cat_name = category.name if category else ""
            tags = (event.tags or "").replace(",", " ")
            desc = event.description or ""
            
            # Combine components (title and category appear twice for higher TF weight)
            content_parts = [
                title, title,
                cat_name, cat_name,
                tags,
                desc
            ]
            doc = " ".join(part for part in content_parts if part).strip()
            
            event_ids.append(event.id)
            documents.append(doc)
            
        return event_ids, documents
    finally:
        db.close()


# ----------------------------------------------------------------------
# Training
# ----------------------------------------------------------------------
def build_content_matrix(documents: list[str]):
    """
    Fits TF-IDF vectorizer on the event documents and returns the matrix.
    """
    logger.info(f"Building TF-IDF matrix for {len(documents)} events...")
    
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2), # Capture bi-grams like "live music", "food festival"
        max_features=5000,
        min_df=1,
    )
    
    tfidf_matrix = vectorizer.fit_transform(documents)
    logger.info(f"Matrix shape: {tfidf_matrix.shape}")
    return vectorizer, tfidf_matrix


# ----------------------------------------------------------------------
# Collaborative Filtering (CF) Training
# ----------------------------------------------------------------------
def build_collaborative_matrix():
    """
    Builds an Item-Item collaborative filtering matrix using user interactions.
    Because data might be very sparse, we aggregate views and reviews into an implicit rating.
    """
    from app.database.connection import SessionLocal
    from app.models.review import Review
    from app.models.interaction import UserInteraction, INTERACTION_SCORES
    import pandas as pd
    from sklearn.decomposition import TruncatedSVD
    from sklearn.preprocessing import normalize
    
    db = SessionLocal()
    try:
        # Load interactions and reviews
        interactions = db.query(UserInteraction).all()
        reviews = db.query(Review).all()
        
        if not interactions and not reviews:
            logger.warning("No interaction/review data found for Collaborative Filtering.")
            return None, None
            
        # Build a list of dicts: {user_id, event_id, score}
        data = []
        # Interactions — use canonical INTERACTION_SCORES from models
        for i in interactions:
            score = INTERACTION_SCORES.get(i.interaction_type, 1.0)
            data.append({"user_id": i.user_id, "event_id": i.event_id, "score": score})
            
        # Reviews (explicit: rating 1-5)
        for r in reviews:
            data.append({"user_id": r.user_id, "event_id": r.event_id, "score": float(r.rating)})
            
        df = pd.DataFrame(data)
        if df.empty:
            return None, None
            
        # Aggregate scores by summing them up if a user interacted multiple times with the same event
        df = df.groupby(['user_id', 'event_id'])['score'].sum().reset_index()
        
        # Create User-Item Matrix
        # Rows = Events, Columns = Users (Because we want item-item similarity)
        ui_matrix = df.pivot(index='event_id', columns='user_id', values='score').fillna(0)
        
        event_ids_cf = ui_matrix.index.to_numpy()
        sparse_matrix = ui_matrix.values
        
        # If we have enough data (at least a few users and items), we can use SVD to reduce noise
        if sparse_matrix.shape[1] > 3 and sparse_matrix.shape[0] > 3:
            logger.info("Applying TruncatedSVD for Collaborative Filtering...")
            n_components = min(20, sparse_matrix.shape[1] - 1)
            svd = TruncatedSVD(n_components=n_components, random_state=42)
            latent_matrix = svd.fit_transform(sparse_matrix)
            # Normalize to make cosine similarity easier later
            cf_features = normalize(latent_matrix, axis=1)
        else:
            logger.info("Not enough data for SVD. Using raw interaction vectors.")
            cf_features = normalize(sparse_matrix, axis=1)
            
        logger.info(f"CF Item-Item Matrix shape: {cf_features.shape}")
        return event_ids_cf, cf_features
        
    finally:
        db.close()

# ----------------------------------------------------------------------
# Save artifacts
# ----------------------------------------------------------------------
def save_artifacts(vectorizer, event_ids: list[int], tfidf_matrix, event_ids_cf=None, cf_matrix=None) -> None:
    """Save vectorizer and event matrices to models/ directory."""
    
    # Save vectorizer
    joblib.dump(vectorizer, TFIDF_PATH)
    
    # Save matrix and IDs together
    matrix_data = {
        "event_ids": np.array(event_ids),
        "tfidf_matrix": tfidf_matrix
    }
    joblib.dump(matrix_data, EVENT_MATRIX_PATH)
    
    logger.info(f"Saved vectorizer → {TFIDF_PATH}")
    # Save CF matrix if available
    if event_ids_cf is not None and cf_matrix is not None:
        cf_data = {
            "event_ids": np.array(event_ids_cf),
            "cf_matrix": cf_matrix
        }
        joblib.dump(cf_data, CF_MATRIX_PATH)
        logger.info(f"Saved CF matrix → {CF_MATRIX_PATH}")
    else:
        logger.info("Skipped saving CF matrix (no data).")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> None:
    print("=" * 60)
    print("NovaTicket — Content-Based Recommender Training")
    print("=" * 60)

    print("\n[1/3] Loading events and building content documents...")
    try:
        event_ids, documents = load_and_prepare_events()
        print(f"  Loaded {len(event_ids)} active events.")
    except Exception as e:
        print(f"  ! DB load failed: {e}")
        sys.exit(1)

    if not event_ids:
        print("\nERROR: No active events found in database.")
        sys.exit(1)

    print("\n[2/4] Training TF-IDF vectorizer (Content-Based)...")
    vectorizer, tfidf_matrix = build_content_matrix(documents)
    
    # Show some top vocabulary terms
    feature_names = vectorizer.get_feature_names_out()
    print(f"  Vocabulary size: {len(feature_names)}")

    print("\n[3/4] Training Collaborative Filtering (Item-Item)...")
    event_ids_cf, cf_matrix = build_collaborative_matrix()
    if event_ids_cf is not None:
        print(f"  CF matrix built for {len(event_ids_cf)} events.")
    else:
        print("  CF matrix skipped due to insufficient data.")

    print("\n[4/4] Saving model artifacts...")
    save_artifacts(vectorizer, event_ids, tfidf_matrix, event_ids_cf, cf_matrix)

    print(f"\n{'=' * 60}")
    print("Training complete!")
    print(f"  Artifacts saved to: {MODELS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
