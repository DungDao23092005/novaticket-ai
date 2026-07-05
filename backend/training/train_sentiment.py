"""
training/train_sentiment.py — Offline Sentiment Model Training Pipeline.

Usage (from backend/ directory, with venv activated):
    python training/train_sentiment.py

What this does:
    1. Load labeled review data from SQL Server DB
    2. Preprocess text using training/utils/text_preprocessor.py
    3. Split into train/test (80/20 stratified)
    4. Fit TF-IDF vectorizer on training set
    5. Train Logistic Regression classifier
    6. Evaluate: Precision, Recall, F1 per class + macro average
    7. Save model artifacts to models/

Output artifacts:
    models/sentiment_model.joblib   — Trained Logistic Regression model
    models/tfidf_sentiment.joblib   — Fitted TF-IDF vectorizer

CRITICAL: The text_preprocessor.preprocess() function used here MUST be
identical to the one used in app/ml/sentiment_model.py at inference time.
Never change preprocessor behavior without retraining.
"""

import sys
import os
from pathlib import Path

# Add backend/ to sys.path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline

from training.utils.text_preprocessor import preprocess


# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
MODELS_DIR = BACKEND_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

SENTIMENT_MODEL_PATH = MODELS_DIR / "sentiment_model.joblib"
TFIDF_PATH = MODELS_DIR / "tfidf_sentiment.joblib"

# Labels (order matters for confusion matrix)
LABELS = ["positive", "neutral", "negative"]


# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------

def load_data_from_db() -> tuple[list[str], list[str]]:
    """
    Load labeled reviews from SQL Server.
    Returns (texts, labels) lists.
    Only returns reviews that have a sentiment_label assigned.
    """
    from app.database.connection import SessionLocal
    from app.models.review import Review

    db = SessionLocal()
    try:
        reviews = (
            db.query(Review)
            .filter(Review.sentiment_label.isnot(None))
            .all()
        )
        texts = [r.content for r in reviews]
        labels = [r.sentiment_label for r in reviews]
        return texts, labels
    finally:
        db.close()


def load_data_from_csv() -> tuple[list[str], list[str]]:
    """
    Fallback: load labeled reviews from seed CSV.
    Used if DB is not available.
    """
    import csv
    csv_path = BACKEND_DIR / "data" / "seed_reviews.csv"

    texts, labels = [], []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["content"].strip().strip('"'))
            labels.append(row["sentiment_label"].strip())
    return texts, labels


# ----------------------------------------------------------------------
# Preprocessing
# ----------------------------------------------------------------------

def prepare_features(texts: list[str]) -> list[str]:
    """Apply text preprocessing pipeline to all texts."""
    return [preprocess(text) for text in texts]


# ----------------------------------------------------------------------
# Training
# ----------------------------------------------------------------------

def train(texts: list[str], labels: list[str]) -> tuple:
    """
    Train TF-IDF + Logistic Regression model.

    Args:
        texts:  List of raw review texts
        labels: List of sentiment labels (positive/neutral/negative)

    Returns:
        (vectorizer, model, X_test_processed, y_test) tuple for evaluation.

    Model config:
        TF-IDF: unigrams + bigrams, max 10k features, min_df=2
        LogReg: C=1.0, max_iter=1000, class_weight='balanced'
            - 'balanced' compensates for class imbalance
            - C=1.0: moderate regularization
    """
    print(f"  Training on {len(texts)} samples...")

    # Preprocess
    processed = prepare_features(texts)

    # Stratified train/test split (preserves class proportions)
    X_train, X_test, y_train, y_test = train_test_split(
        processed,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )
    print(f"  Train: {len(X_train)}, Test: {len(X_test)}")

    # TF-IDF Vectorizer
    # ngram_range=(1,2): unigrams + bigrams (captures "not good", "very bad")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=10_000,
        min_df=2,          # Ignore terms in fewer than 2 documents
        sublinear_tf=True, # Apply log(1+tf) instead of raw tf
    )

    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Logistic Regression
    model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight="balanced",  # Handles class imbalance automatically
        random_state=42,
        solver="lbfgs",
        multi_class="multinomial",
    )
    model.fit(X_train_vec, y_train)

    return vectorizer, model, X_test_vec, y_test


# ----------------------------------------------------------------------
# Evaluation
# ----------------------------------------------------------------------

def evaluate(model, X_test, y_test: list[str]) -> dict:
    """
    Evaluate the trained model on the test set.

    Returns a dict with per-class and macro-average metrics.
    Prints a formatted classification report to stdout.
    """
    y_pred = model.predict(X_test)

    print("\n  === Classification Report ===")
    report = classification_report(
        y_test,
        y_pred,
        labels=LABELS,
        digits=3,
    )
    print(report)

    print("  === Confusion Matrix ===")
    print(f"  Labels: {LABELS}")
    cm = confusion_matrix(y_test, y_pred, labels=LABELS)
    print(f"  {cm}")

    # Parse metrics for return
    from sklearn.metrics import precision_recall_fscore_support
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, labels=LABELS, average="macro", zero_division=0
    )

    return {
        "macro_precision": round(float(precision), 4),
        "macro_recall": round(float(recall), 4),
        "macro_f1": round(float(f1), 4),
        "test_size": len(y_test),
    }


# ----------------------------------------------------------------------
# Save artifacts
# ----------------------------------------------------------------------

def save_artifacts(vectorizer, model) -> None:
    """Save trained vectorizer and model to models/ directory."""
    joblib.dump(vectorizer, TFIDF_PATH)
    joblib.dump(model, SENTIMENT_MODEL_PATH)
    print(f"\n  Saved vectorizer → {TFIDF_PATH}")
    print(f"  Saved model      → {SENTIMENT_MODEL_PATH}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("NovaTicket — Sentiment Model Training")
    print("=" * 60)

    # Load data — try DB first, fallback to CSV
    print("\n[1/4] Loading data...")
    try:
        texts, labels = load_data_from_db()
        source = "SQL Server DB"
    except Exception as e:
        print(f"  ! DB load failed ({e}), falling back to CSV")
        texts, labels = load_data_from_csv()
        source = "seed_reviews.csv"

    print(f"  Loaded {len(texts)} labeled reviews from {source}")

    # Label distribution
    from collections import Counter
    dist = Counter(labels)
    print(f"  Distribution: {dict(dist)}")

    if len(texts) < 20:
        print("\nERROR: Not enough data to train. Need at least 20 labeled reviews.")
        print("Run: python data/seed.py  to seed review data first.")
        sys.exit(1)

    # Train
    print("\n[2/4] Training TF-IDF + Logistic Regression...")
    vectorizer, model, X_test, y_test = train(texts, labels)

    # Evaluate
    print("\n[3/4] Evaluating on test set...")
    metrics = evaluate(model, X_test, y_test)
    print(f"\n  Macro F1: {metrics['macro_f1']:.3f}")
    print(f"  Macro Precision: {metrics['macro_precision']:.3f}")
    print(f"  Macro Recall: {metrics['macro_recall']:.3f}")

    # Save
    print("\n[4/4] Saving model artifacts...")
    save_artifacts(vectorizer, model)

    print(f"\n{'=' * 60}")
    print("Training complete!")
    print(f"  Model saved to: {MODELS_DIR}")
    print(f"  Macro F1 score: {metrics['macro_f1']:.3f}")

    if metrics["macro_f1"] < 0.60:
        print("\n  WARNING: Macro F1 < 0.60 — model quality is low.")
        print("  Consider: adding more labeled data, tuning hyperparameters.")
    elif metrics["macro_f1"] >= 0.80:
        print("\n  EXCELLENT: Macro F1 >= 0.80 — model is production ready.")
    else:
        print("\n  ACCEPTABLE: Macro F1 >= 0.60 — model is usable.")
    print("=" * 60)


if __name__ == "__main__":
    main()
