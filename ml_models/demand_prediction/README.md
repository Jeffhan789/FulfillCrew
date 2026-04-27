# Demand Prediction Model

First MVP version exposes an inference function shaped like an MLP regression model output. It can be replaced by a trained PyTorch, TensorFlow or scikit-learn MLP later.

Input features:

- price
- quantity
- rating
- category
- type
- previous sales features

Output:

- predicted sales for the next 7 days

