"""Evaluate the trained TF-IDF + Logistic Regression product category classifier.

Usage:
    python -m ml_models.product_category_classifier.evaluate
"""

import json
import pickle
from pathlib import Path
from typing import Dict

from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report

from ml_models.product_category_classifier.train import load_products, extract_features, train_classifier


def evaluate_model() -> Dict:
    """Load trained model and evaluate on test set.

    Returns:
        Dictionary with evaluation metrics.
    """
    model_dir = Path(__file__).parent / "models"

    # Load artifacts
    with open(model_dir / "vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    with open(model_dir / "classifier.pkl", "rb") as f:
        classifier = pickle.load(f)
    with open(model_dir / "categories.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

    # Load data and re-create the same train/test split
    products = load_products()
    texts, labels = extract_features(products)
    _, _, X_train, X_test, y_train, y_test = train_classifier(texts, labels)

    # Evaluate on test set
    X_test_vec = vectorizer.transform(X_test)
    y_pred = classifier.predict(X_test_vec)

    accuracy = accuracy_score(y_test, y_pred)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, y_pred, labels=categories, zero_division=0
    )

    per_class = {}
    for i, cat in enumerate(categories):
        per_class[cat] = {
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1_score": float(f1[i]),
            "support": int(support[i]),
        }

    results = {
        "accuracy": float(accuracy),
        "num_test_samples": len(y_test),
        "per_class": per_class,
        "classification_report": classification_report(y_test, y_pred, zero_division=0),
    }

    return results


def main() -> None:
    """Main evaluation entrypoint."""
    print("Evaluating trained model...\n")
    results = evaluate_model()

    print(f"Accuracy: {results['accuracy']:.4f}")
    print(f"Test samples: {results['num_test_samples']}\n")

    print("Per-class metrics:")
    for cat, metrics in results["per_class"].items():
        print(
            f"  {cat:15s}  "
            f"Precision: {metrics['precision']:.4f}  "
            f"Recall: {metrics['recall']:.4f}  "
            f"F1: {metrics['f1_score']:.4f}  "
            f"Support: {metrics['support']}"
        )

    print("\nDetailed classification report:")
    print(results["classification_report"])

    # Save results
    model_dir = Path(__file__).parent / "models"
    eval_path = model_dir / "evaluation.json"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Evaluation results saved to {eval_path}")


if __name__ == "__main__":
    main()
