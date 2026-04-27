import math


class LightweightDemandMLP:
    """Small deterministic MLP-shaped regressor for MVP inference."""

    def __init__(self) -> None:
        self.weights = [0.018, -0.025, 0.75, 0.32, 0.2]
        self.bias = 2.5

    def predict(self, features: list[float]) -> int:
        activation = self.bias + sum(weight * value for weight, value in zip(self.weights, features))
        hidden = max(0.0, activation)
        output = 1 + 6 / (1 + math.exp(-hidden / 4))
        return max(1, int(round(output)))

