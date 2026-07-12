"""Keyword-based heuristic fallback classifier for product categories."""

KEYWORDS = {
    "electronics": {"watch", "headphone", "wireless", "smart", "device", "audio"},
    "home": {"lamp", "desk", "chair", "kitchen", "light"},
    "fashion": {"shirt", "shoe", "jacket", "wearable"},
    "sports": {"ball", "fitness", "training", "equipment"},
    "beauty": {"skin", "cream", "care"},
    "books": {"book", "paperback", "novel"},
}


def classify_category(name: str) -> str:
    """Classify a product by keyword matching.

    Args:
        name: Product name string.

    Returns:
        Predicted category string. Defaults to "electronics" if no keywords match.
    """
    tokens = set(name.lower().split())
    scores = {category: len(tokens & words) for category, words in KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "electronics"
