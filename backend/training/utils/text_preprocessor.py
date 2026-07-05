"""
training/utils/text_preprocessor.py — Text preprocessing for Sentiment ML pipeline.

Provides a clean, reusable preprocessing pipeline:
    - Shared between training (train_sentiment.py) and inference (app/ml/sentiment_model.py)
    - Must be IDENTICAL in both contexts — training and serving must use same transform

Functions:
    clean(text)       → lowercase, remove noise, normalize whitespace
    tokenize(text)    → split cleaned text into tokens
    preprocess(text)  → full pipeline: clean → remove stopwords → join back to string

Usage:
    from training.utils.text_preprocessor import preprocess

    text = "Amazing event!! The speakers were GREAT 🎉"
    clean_text = preprocess(text)
    # → "amazing event speakers great"
"""

import re
import string
from typing import Final

# -----------------------------------------------------------------------
# Stopwords — manually curated minimal set
# Rationale: Using nltk/spaCy adds heavy dependencies.
# For sentiment, we keep negations (not, never, no) as they flip polarity.
# -----------------------------------------------------------------------
STOPWORDS: Final[frozenset[str]] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "that", "this",
    "these", "those", "i", "me", "my", "we", "our", "you", "your", "they",
    "their", "it", "its", "he", "she", "him", "her", "his", "we", "us",
    "am", "also", "just", "so", "then", "than", "which", "who", "what",
    "when", "where", "how", "if", "because", "although", "while", "after",
    "before", "about", "into", "through", "during", "each", "all", "any",
    "both", "few", "more", "most", "other", "some", "such", "only", "own",
    "same", "too", "very", "can", "there",
    # NOTE: "not", "never", "no", "nothing", "nobody" are intentionally KEPT
    # because they are critical for sentiment polarity
})


def clean(text: str) -> str:
    """
    Normalize text for ML processing.

    Steps:
        1. Lowercase
        2. Remove URLs (http/https links)
        3. Remove email addresses
        4. Remove emojis and non-ASCII characters
        5. Remove punctuation (keep letters, digits, spaces)
        6. Collapse multiple whitespace to single space
        7. Strip leading/trailing whitespace

    Args:
        text: Raw input text (review content)

    Returns:
        Cleaned, normalized string.

    Examples:
        >>> clean("Amazing event!! Visit https://example.com 🎉")
        "amazing event visit"

        >>> clean("NOT good at all... very BORING")
        "not good at all very boring"
    """
    if not text or not text.strip():
        return ""

    # 1. Lowercase
    text = text.lower()

    # 2. Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # 3. Remove emails
    text = re.sub(r"\S+@\S+", " ", text)

    # 4. Remove non-ASCII (emojis, special unicode characters)
    text = text.encode("ascii", errors="ignore").decode("ascii")

    # 5. Remove punctuation — keep letters, digits, spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # 6. Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    # 7. Strip
    return text.strip()


def tokenize(text: str) -> list[str]:
    """
    Split cleaned text into tokens (words).

    Args:
        text: Pre-cleaned text (output of clean())

    Returns:
        List of word tokens. Empty list if text is empty.

    Example:
        >>> tokenize("amazing event speakers great")
        ["amazing", "event", "speakers", "great"]
    """
    if not text:
        return []
    return text.split()


def remove_stopwords(tokens: list[str]) -> list[str]:
    """
    Remove common stopwords from token list.
    Negations (not, never, no) are intentionally kept for sentiment accuracy.

    Args:
        tokens: List of tokens from tokenize()

    Returns:
        Filtered list of tokens with stopwords removed.
    """
    return [token for token in tokens if token not in STOPWORDS]


def preprocess(text: str, *, keep_stopwords: bool = False) -> str:
    """
    Full preprocessing pipeline: clean → tokenize → remove stopwords → join.

    This is the MAIN function used by both:
        - training/train_sentiment.py  (fitting the vectorizer)
        - app/ml/sentiment_model.py    (serving predictions)

    CRITICAL: Must produce identical output in training and inference.
    Never change this function after model is trained without retraining.

    Args:
        text: Raw review text
        keep_stopwords: If True, skip stopword removal (rarely needed)

    Returns:
        Preprocessed string ready for TF-IDF vectorization.

    Examples:
        >>> preprocess("Amazing event! The speakers were GREAT!")
        "amazing event speakers great"

        >>> preprocess("Not good, very boring experience")
        "not good very boring experience"
    """
    cleaned = clean(text)
    tokens = tokenize(cleaned)

    if not keep_stopwords:
        tokens = remove_stopwords(tokens)

    return " ".join(tokens)
