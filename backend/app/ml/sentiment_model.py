"""
app/ml/sentiment_model.py — Sentiment Model Inference (Singleton Pattern).

Loads trained model artifacts once at module import time (not per-request).
Provides a single predict() function used by SentimentService.

Design decisions:
    - Singleton: vectorizer + model loaded once → reused across all requests
    - Graceful degradation: if artifact files missing, is_loaded() returns False
      and the API continues to run (review saved without sentiment label)
    - Uses SAME preprocess() as training — NEVER change without retraining
    - predict() returns (label, confidence) where confidence = max class probability

Artifact paths (relative to backend/):
    models/sentiment_model.joblib   — Logistic Regression model
    models/tfidf_sentiment.joblib   — TF-IDF vectorizer

Usage:
    from app.ml.sentiment_model import sentiment_model

    if sentiment_model.is_loaded():
        label, confidence = sentiment_model.predict("Amazing event!")
        # label = "positive", confidence = 0.92
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Paths relative to backend/ directory
_BACKEND_DIR = Path(__file__).parent.parent.parent
_MODELS_DIR = _BACKEND_DIR / "models"
_MODEL_PATH = _MODELS_DIR / "sentiment_model.joblib"
_TFIDF_PATH = _MODELS_DIR / "tfidf_sentiment.joblib"

# Valid labels (must match training labels)
SENTIMENT_LABELS = ["positive", "neutral", "negative"]


class SentimentModel:
    """
    Singleton wrapper around TF-IDF + LogReg sentiment classifier.

    Loads artifacts on instantiation. Provides predict() for inference.
    Handles missing artifacts gracefully — API continues without sentiment.
    """

    def __init__(self) -> None:
        self._vectorizer = None
        self._model = None
        self._loaded = False
        self._load()

    def _load(self) -> None:
        """
        Load model artifacts from disk.
        Called once at module import. Silently fails if files not found.
        """
        try:
            import joblib

            if not _MODEL_PATH.exists():
                logger.warning(
                    "Sentiment model not found at %s. "
                    "Run: python training/train_sentiment.py",
                    _MODEL_PATH,
                )
                return

            if not _TFIDF_PATH.exists():
                logger.warning(
                    "TF-IDF vectorizer not found at %s. "
                    "Run: python training/train_sentiment.py",
                    _TFIDF_PATH,
                )
                return

            self._vectorizer = joblib.load(_TFIDF_PATH)
            self._model = joblib.load(_MODEL_PATH)
            self._loaded = True
            logger.info("Sentiment model loaded successfully from %s", _MODELS_DIR)

        except Exception as exc:
            logger.error("Failed to load sentiment model: %s", exc)
            self._loaded = False

    def is_loaded(self) -> bool:
        """Return True if model and vectorizer are both loaded and ready."""
        return self._loaded

    def predict(self, text: str) -> tuple[str, float]:
        """
        Predict sentiment label and confidence for a given text.

        IMPORTANT: Uses the same preprocess() function as training.
        The text is preprocessed before vectorization — never skip this step.

        Args:
            text: Raw review text (not preprocessed)

        Returns:
            (label, confidence) where:
                label:      "positive" | "neutral" | "negative"
                confidence: float in [0.0, 1.0] — max class probability

        Raises:
            RuntimeError: If model is not loaded (check is_loaded() first)

        Example:
            label, conf = sentiment_model.predict("Fantastic event!")
            # → ("positive", 0.94)

            label, conf = sentiment_model.predict("Terrible experience!")
            # → ("negative", 0.88)
        """
        if not self._loaded:
            raise RuntimeError(
                "Sentiment model is not loaded. "
                "Run python training/train_sentiment.py to train the model."
            )

        # Import here to avoid circular imports and keep startup fast
        from training.utils.text_preprocessor import preprocess

        # Preprocess text (same pipeline as training — critical for consistency)
        processed = preprocess(text)

        # Vectorize + predict
        X = self._vectorizer.transform([processed])
        label: str = self._model.predict(X)[0]

        # Get confidence = max probability across all classes
        proba = self._model.predict_proba(X)[0]
        confidence: float = float(proba.max())

        return label, round(confidence, 4)


# Module-level singleton — instantiated once at import time
# All callers share the same loaded model instance
sentiment_model = SentimentModel()
