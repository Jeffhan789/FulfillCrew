# Neural Network Models

The MVP uses lightweight deterministic models with stable inference contracts. This keeps the system runnable before collecting a larger training dataset.

## Demand Prediction

Input:

- price
- quantity
- rating
- category indicator
- type indicator

Output:

- predicted demand for the next 7 days

Future upgrade: train a real MLP regression model using historical sales records.

## Fraud Detection

Input:

- order total
- number of items
- average item price
- new user flag
- shipping distance

Output:

- risk score from 0 to 1

Future upgrade: compare an SVM baseline against an MLP binary classifier.

