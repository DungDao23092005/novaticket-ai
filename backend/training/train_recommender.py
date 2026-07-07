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
    models/tfidf_content.joblib   — Fitted TF-IDF vectorizer
    models/event_matrix.joblib    — Dictionary containing:
                                      - "event_ids": numpy array of event IDs matching matrix rows
                                      - "tfidf_matrix": sparse TF-IDF matrix of all events

These artifacts are loaded at startup by the inference service to provide
content-based recommendations in real-time.
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
        events = db.query(Event, Category).join(Category, Event.category_id == Category.id).filter(Event.is_active == True).all()
        
        for event, category in events:
            # Construct a rich text document for content-based filtering
            # We weight title and category higher by repeating them
            title = event.title or ""
            cat_name = category.name or ""
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
# Save artifacts
# ----------------------------------------------------------------------
def save_artifacts(vectorizer, event_ids: list[int], tfidf_matrix) -> None:
    """Save vectorizer and event matrix to models/ directory."""
    
    # Save vectorizer
    joblib.dump(vectorizer, TFIDF_PATH)
    
    # Save matrix and IDs together
    matrix_data = {
        "event_ids": np.array(event_ids),
        "tfidf_matrix": tfidf_matrix
    }
    joblib.dump(matrix_data, EVENT_MATRIX_PATH)
    
    logger.info(f"Saved vectorizer → {TFIDF_PATH}")
    logger.info(f"Saved event matrix → {EVENT_MATRIX_PATH}")


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

    print("\n[2/3] Training TF-IDF vectorizer...")
    vectorizer, tfidf_matrix = build_content_matrix(documents)
    
    # Show some top vocabulary terms
    feature_names = vectorizer.get_feature_names_out()
    print(f"  Vocabulary size: {len(feature_names)}")
    if len(feature_names) > 0:
        sample_terms = np.random.choice(feature_names, min(5, len(feature_names)), replace=False)
        print(f"  Sample terms: {', '.join(sample_terms)}")

    print("\n[3/3] Saving model artifacts...")
    save_artifacts(vectorizer, event_ids, tfidf_matrix)

    print(f"\n{'=' * 60}")
    print("Training complete!")
    print(f"  Artifacts saved to: {MODELS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
