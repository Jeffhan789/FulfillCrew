"""Product category prediction with TF-IDF + Logistic Regression.

Provides a backward-compatible ``predict_category`` function and a new
``CategoryClassifier`` class with probability support.
"""

import pickle
import json
from pathlib import Path

from typing import Dict, List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from ml_models.product_category_classifier.model import classify_category


class CategoryClassifier:
    """TF-IDF + Logistic Regression product category classifier.

    Attempts to load a trained model from disk. If the model files are missing,
    falls back to the keyword-based heuristic classifier.
    """

    def __init__(self, model_dir: Optional[str] = None) -> None:
        """Initialize the classifier.

        Args:
            model_dir: Directory containing ``vectorizer.pkl``,
                ``classifier.pkl``, and ``categories.json``. Defaults to the
                ``models/`` sibling directory.
        """
        if model_dir is None:
            model_dir = Path(__file__).parent / "models"
        self.model_dir = Path(model_dir)
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.classifier: Optional[LogisticRegression] = None
        self.categories: Optional[List[str]] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load trained model from disk or fallback to heuristic."""
        vectorizer_path = self.model_dir / "vectorizer.pkl"
        classifier_path = self.model_dir / "classifier.pkl"
        categories_path = self.model_dir / "categories.json"

        if not all(p.exists() for p in (vectorizer_path, classifier_path, categories_path)):
            print(f"[CategoryClassifier] Model files not found in {self.model_dir}. Using heuristic fallback.")
            self.categories = None
            return

        try:
            with open(vectorizer_path, "rb") as f:
                self.vectorizer = pickle.load(f)
            with open(classifier_path, "rb") as f:
                self.classifier = pickle.load(f)
            with open(categories_path, "r", encoding="utf-8") as f:
                self.categories = json.load(f)
        except Exception as exc:
            print(f"[CategoryClassifier] Failed to load model ({exc}). Using heuristic fallback.")
            self.vectorizer = None
            self.classifier = None
            self.categories = None

    def _model_available(self) -> bool:
        """Return True if the ML model is loaded and ready."""
        return self.vectorizer is not None and self.classifier is not None and self.categories is not None

    def predict(self, product_name: str) -> str:
        """Predict category from product name.

        Args:
            product_name: The product name text.

        Returns:
            Predicted category string.
        """
        name = str(product_name).strip()
        if not name:
            return "unknown"

        if self._model_available():
            vec = self.vectorizer.transform([name])
            pred = self.classifier.predict(vec)[0]
            return str(pred)

        # Fallback to heuristic keyword classifier
        return classify_category(name)

    def predict_proba(self, product_name: str) -> Dict[str, float]:
        """Return category probabilities for the given product name.

        If the ML model is unavailable, the heuristic fallback returns a
        dictionary with the predicted category at probability 1.0 and all
        others at 0.0.

        Args:
            product_name: The product name text.

        Returns:
            Mapping from category name to probability (float).
        """
        name = str(product_name).strip()
        if not name:
            return {"unknown": 1.0}

        if self._model_available():
            vec = self.vectorizer.transform([name])
            probs = self.classifier.predict_proba(vec)[0]
            return {cat: float(prob) for cat, prob in zip(self.categories, probs)}

        # Fallback: heuristic returns 1.0 for the chosen category, 0.0 for others
        pred = classify_category(name)
        fallback = {cat: 0.0 for cat in (self.categories or [])}
        if fallback:
            fallback[pred] = 1.0
        else:
            fallback = {pred: 1.0}
        return fallback


def predict_category(product: dict) -> str:
    """Legacy compatibility function.

    Args:
        product: Product dictionary with at least a ``name`` key.

    Returns:
        Predicted category string.
    """
    classifier = CategoryClassifier()
    return classifier.predict(str(product.get("name", "")))
