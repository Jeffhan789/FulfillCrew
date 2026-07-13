"""PyTorch MLP for demand prediction (ELEC320 Neural Networks).

Architecture: 2-layer Multi-Layer Perceptron (MLP) with ReLU activations
and Dropout regularisation.

Input Features (9-dimensional):
    1. price              — Product unit price
    2. rating             — Customer rating (1-5)
    3. category_encoded   — One-hot or label-encoded category
    4. type_encoded       — One-hot or label-encoded sub-type
    5. day_of_week        — 0=Monday ... 6=Sunday
    6. month              — 1=January ... 12=December
    7. is_weekend         — Binary flag
    8. sales_last_7_days  — Rolling window sales
    9. sales_last_30_days — Longer rolling window sales

Network Topology:
    Input(9) → Linear(9→64) → ReLU → Dropout(0.2)
             → Linear(64→32) → ReLU → Dropout(0.2)
             → Linear(32→1)  → Output (scalar regression)

Design Decisions:
    - Dropout(0.2): Prevents overfitting by randomly zeroing 20% of neurons
      during training. Disabled during inference (model.eval()).
    - ReLU: Non-linear activation that avoids vanishing gradients
      (unlike sigmoid/tanh in deep networks).
    - squeeze(-1): Flattens the final (batch, 1) tensor to (batch,) for
      compatibility with MSELoss.

Engineering Note:
    Q: Why 64→32 instead of 128→64→32?
    A: Demand prediction with 9 features is a relatively simple regression
       problem. A deeper network would overfit on limited training data.
       64→32 is a good balance between model capacity and generalisation.
       
    Q: What loss function and optimizer would you use?
    A: MSELoss (Mean Squared Error) for regression. Adam optimizer with
       learning rate 1e-3 and weight decay 1e-5 for regularisation.
       See ml_models/demand_prediction/train.py for the full training loop.
"""

import torch
import torch.nn as nn


class DemandMLP(nn.Module):
    """2-layer MLP for demand prediction.

    Input: 9-dimensional feature vector
        - price, rating, category_encoded, type_encoded,
          day_of_week, month, is_weekend,
          sales_last_7_days, sales_last_30_days
    Output: scalar predicted next 7-day sales.
    """

    def __init__(self, input_dim: int = 9) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning a 1-D tensor of shape (batch_size,)."""
        return self.net(x).squeeze(-1)
