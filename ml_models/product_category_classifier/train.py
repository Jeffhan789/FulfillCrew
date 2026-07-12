"""Train a TF-IDF + Logistic Regression product category classifier.

Usage:
    python -m ml_models.product_category_classifier.train
"""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report


def _project_root() -> Path:
    """Return the project root directory."""
    # This file is at: ml_models/product_category_classifier/train.py
    return Path(__file__).parent.parent.parent


def load_products() -> List[Dict]:
    """Load cleaned product data from JSON."""
    data_path = _project_root() / "data_cleaning" / "cleaned_products" / "products.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_features(products: List[Dict]) -> Tuple[List[str], List[str]]:
    """Extract text features (name) and labels (category) from products.

    Returns:
        Tuple of (names, categories).
    """
    names = [str(p.get("name", "")) for p in products]
    categories = [str(p.get("category", "unknown")) for p in products]
    return names, categories


def train_classifier(
    texts: List[str],
    labels: List[str],
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[TfidfVectorizer, LogisticRegression, List[str], List[str], List[str], List[str]]:
    """Train TF-IDF + Logistic Regression classifier.

    Returns:
        Tuple of (vectorizer, classifier, X_train, X_test, y_train, y_test).
    """
    # Split data; stratify if possible to preserve class distribution
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=test_size, random_state=random_state, stratify=labels
        )
    except ValueError:
        # Too few samples for stratification; fall back to non-stratified split
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=test_size, random_state=random_state
        )

    vectorizer = TfidfVectorizer(max_features=1000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    classifier = LogisticRegression(multi_class="multinomial", max_iter=1000, random_state=random_state)
    classifier.fit(X_train_vec, y_train)

    return vectorizer, classifier, X_train, X_test, y_train, y_test


def save_model(
    vectorizer: TfidfVectorizer,
    classifier: LogisticRegression,
    categories: List[str],
    model_dir: Path,
) -> None:
    """Save trained artifacts to disk."""
    model_dir.mkdir(parents=True, exist_ok=True)

    with open(model_dir / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    with open(model_dir / "classifier.pkl", "wb") as f:
        pickle.dump(classifier, f)

    with open(model_dir / "categories.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)


def main() -> None:
    """Main training entrypoint."""
    print("Loading product data...")
    products = load_products()
    print(f"Loaded {len(products)} products.")

    if len(products) < 2:
        raise RuntimeError("Insufficient data to train a classifier (need at least 2 products).")

    texts, labels = extract_features(products)

    print("Training TF-IDF + Logistic Regression classifier...")
    vectorizer, classifier, X_train, X_test, y_train, y_test = train_classifier(texts, labels)

    # Quick sanity check on training data
    train_vec = vectorizer.transform(X_train)
    train_pred = classifier.predict(train_vec)
    print(f"Training accuracy: {accuracy_score(y_train, train_pred):.4f}")

    print("\nClassification report on training data:")
    print(classification_report(y_train, train_pred, zero_division=0))

    categories = sorted(set(labels))
    model_dir = Path(__file__).parent / "models"
    save_model(vectorizer, classifier, categories, model_dir)
    print(f"\nModel artifacts saved to {model_dir}")
    print("  - vectorizer.pkl")
    print("  - classifier.pkl")
    print("  - categories.json")


if __name__ == "__main__":
    main()
