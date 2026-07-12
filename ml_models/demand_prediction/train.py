"""Generate synthetic training data and train a PyTorch MLP for demand prediction."""

import json
import math
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from ml_models.demand_prediction.model import DemandMLP


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent
PRODUCTS_PATH = PROJECT_ROOT / "data_cleaning" / "cleaned_products" / "products.json"
MODEL_SAVE_DIR = Path(__file__).parent / "models"
MODEL_SAVE_PATH = MODEL_SAVE_DIR / "demand_mlp.pt"

RANDOM_SEED = 42
N_SAMPLES = 2000
TRAIN_SPLIT = 0.8
BATCH_SIZE = 32
EPOCHS = 50
LEARNING_RATE = 0.001

CATEGORY_MAP = {
    "electronics": 1.0,
    "home": 0.5,
}

TYPE_MAP = {
    "device": 1.0,
    "audio": 0.8,
    "lighting": 0.6,
}


def set_seed(seed: int = RANDOM_SEED) -> None:
    """Fix random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_products(path: Path = PRODUCTS_PATH) -> List[Dict]:
    """Load product data from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_synthetic_data(
    products: List[Dict], n_samples: int = N_SAMPLES
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic training samples from the base product catalogue.

    Each sample is a 9-dimensional feature vector and a scalar target
    (next_7_day_sales).  Features are derived from real product attributes
    with additive/multiplicative noise so the model learns generalisable
    patterns rather than memorising the 4 original rows.
    """
    features: List[List[float]] = []
    targets: List[float] = []

    for _ in range(n_samples):
        # 1. Pick a base product and perturb its continuous attributes
        base = random.choice(products)

        price = max(1.0, float(base.get("price", 50)) * random.uniform(0.5, 2.0))
        rating = np.clip(
            float(base.get("rating", 3.0)) + random.uniform(-0.5, 0.5), 1.0, 5.0
        )
        quantity = max(0, int(float(base.get("quantity", 10)) * random.uniform(0, 3)))

        category = base.get("category", "home")
        type_ = base.get("type", "device")
        category_enc = CATEGORY_MAP.get(category, 0.5)
        type_enc = TYPE_MAP.get(type_, 0.6)

        # 2. Temporal features
        day_of_week = random.randint(0, 6)
        month = random.randint(1, 12)
        is_weekend = 1.0 if day_of_week in (5, 6) else 0.0

        # 3. Historical sales (correlated with the true demand we are about to generate)
        price_sensitivity = math.exp(-price / 100.0)          # higher price → lower demand
        rating_boost = 1.0 + (rating - 3.0) / 5.0            # higher rating → higher demand
        seasonal_factor = 1.0 + 0.1 * math.sin(2 * math.pi * month / 12.0)
        weekend_boost = 1.2 if is_weekend else 1.0
        category_boost = 1.5 if category == "electronics" else 1.0
        type_boost = 1.2 if type_ == "device" else 1.0 if type_ == "audio" else 0.8

        base_demand = (
            50.0
            * price_sensitivity
            * rating_boost
            * seasonal_factor
            * weekend_boost
            * category_boost
            * type_boost
        )

        # Add stock-influence noise so quantity is not the only signal
        target = base_demand + quantity * 0.1 + random.gauss(0, 3.0)
        target = max(0.0, target)

        sales_last_7 = max(0.0, target * 0.7 + random.gauss(0, 2.0))
        sales_last_30 = max(0.0, target * 3.0 + random.gauss(0, 5.0))

        feature_vec = [
            price,
            rating,
            category_enc,
            type_enc,
            float(day_of_week),
            float(month),
            is_weekend,
            sales_last_7,
            sales_last_30,
        ]

        features.append(feature_vec)
        targets.append(target)

    return np.array(features, dtype=np.float32), np.array(targets, dtype=np.float32)


class DemandDataset(Dataset):
    """PyTorch Dataset wrapping synthetic demand features and targets."""

    def __init__(self, X: np.ndarray, y: np.ndarray) -> None:
        self.X = torch.from_numpy(X)
        self.y = torch.from_numpy(y)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]


def train() -> None:
    """End-to-end training pipeline: generate data, train, save model."""
    set_seed()

    # ------------------------------------------------------------------
    # 1. Load raw products and generate synthetic data
    # ------------------------------------------------------------------
    products = load_products()
    X, y = generate_synthetic_data(products, n_samples=N_SAMPLES)

    print(f"Generated {len(X)} synthetic samples.")
    print(f"  Feature means: {X.mean(axis=0).round(2).tolist()}")
    print(f"  Target range:  [{y.min():.2f}, {y.max():.2f}]")

    # ------------------------------------------------------------------
    # 2. Train / test split
    # ------------------------------------------------------------------
    split_idx = int(len(X) * TRAIN_SPLIT)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    train_dataset = DemandDataset(X_train, y_train)
    test_dataset = DemandDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    # ------------------------------------------------------------------
    # 3. Model, loss, optimizer
    # ------------------------------------------------------------------
    model = DemandMLP(input_dim=9)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # ------------------------------------------------------------------
    # 4. Training loop
    # ------------------------------------------------------------------
    for epoch in range(1, EPOCHS + 1):
        model.train()
        epoch_losses: List[float] = []

        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())

        avg_loss = sum(epoch_losses) / len(epoch_losses)

        if epoch == 1 or epoch % 10 == 0 or epoch == EPOCHS:
            model.eval()
            test_losses: List[float] = []
            with torch.no_grad():
                for batch_x, batch_y in test_loader:
                    preds = model(batch_x)
                    test_losses.append(criterion(preds, batch_y).item())
            avg_test_loss = sum(test_losses) / len(test_losses)
            print(
                f"Epoch {epoch:03d}/{EPOCHS} — "
                f"train MSE: {avg_loss:.4f} | test MSE: {avg_test_loss:.4f}"
            )

    # ------------------------------------------------------------------
    # 5. Save model
    # ------------------------------------------------------------------
    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print(f"Model saved to {MODEL_SAVE_PATH}")


if __name__ == "__main__":
    train()
