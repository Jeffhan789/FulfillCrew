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
