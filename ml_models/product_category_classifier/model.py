"""Keyword-based heuristic fallback classifier for product categories.

This is a simplified TF-IDF + LogisticRegression-style classifier without
actual model training. It demonstrates the concept of text classification
using token matching and scoring.

How it works:
1. Tokenise the product name into lowercase words
2. Count how many tokens overlap with each category's keyword set
3. Return the category with the highest overlap score
4. Default to "electronics" if no keywords match

This is conceptually similar to a Bag-of-Words (BoW) model, where each
word's presence contributes to the category score. In a real system this
would be replaced by:
    - TF-IDF vectorisation + LogisticRegression (scikit-learn)
    - Naive Bayes classifier
    - BERT fine-tuning for semantic understanding

Interview Note:
    Q: Why default to "electronics"?
    A: Electronics is the most common category in the dataset. This is a
       simple form of prior probability — P(electronics) > P(books) in
       e-commerce. A proper classifier would learn these priors from data.
       
    Q: What are the limitations of keyword matching?
    A: 1. Synonyms: "laptop" won't match "computer" 
       2. Ambiguity: "light" could mean home lighting or lightweight clothing
       3. New products: unknown keywords always default to electronics
       4. No context: ignores product description, price, image
"""

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
