# ML Models

This directory contains the AI prediction layer of FulfillCrew. All three modules expose stable inference interfaces that can be replaced by trained PyTorch, TensorFlow, or scikit-learn models without changing the agent code that calls them.

## Design Philosophy

The first version uses lightweight deterministic models so the entire system can run immediately without downloading weights or training data. Each module follows the same interface contract:

- `model.py` — Defines the model logic (or a lightweight placeholder).
- `predict.py` — Exposes a simple `predict_*` function that the backend agents import.
- `train.py` — A training script placeholder that documents how to replace the lightweight model with a real trained version.

## Modules

| Module | Course Topic | Task | Current Implementation |
|--------|-------------|------|----------------------|
| `demand_prediction/` | MLP regression | Predict next 7-day sales from product features | `LightweightDemandMLP` deterministic regressor |
| `fraud_detection/` | Binary classification | Score order risk from 0 to 1 | `LightweightFraudClassifier` logistic-style scorer |
| `product_category_classifier/` | Supervised classification | Map product name to category label | Keyword-based rule classifier |

## How Agents Use These Modules

- `DemandPredictionAgent.predict()` calls `predict_demand(product)` for each product in the basket and sums the results.
- `FraudDetectionAgent.score()` calls `predict_risk(features)` with order-level features.
- The backend does not yet call `predict_category()` in the main order flow, but the module is ready for product catalog enrichment and auto-repair.

## Upgrade Path

For each module, the intended evolution is:

1. Collect real historical data (or generate a realistic synthetic dataset).
2. Implement model training in `train.py` (PyTorch `nn.Module`, scikit-learn `MLPRegressor`, etc.).
3. Save trained weights to a file (e.g., `.pt`, `.pkl`, `.joblib`).
4. Update `predict.py` to load the trained weights and run inference.
5. The agent code that imports `predict.py` does not need to change.

---

# ML 模型（ML Models）

本目录包含 FulfillCrew 的 AI 预测层。三个模块都暴露了稳定的推理接口，可以在不修改调用它们的智能体代码的前提下，替换为训练后的 PyTorch、TensorFlow 或 scikit-learn 模型。

## 设计哲学

第一版使用轻量级确定性模型，使得整个系统无需下载权重或训练数据即可立即运行。每个模块遵循相同的接口契约：

- `model.py` — 定义模型逻辑（或轻量级占位实现）。
- `predict.py` — 暴露简单的 `predict_*` 函数，供后端智能体导入。
- `train.py` — 训练脚本占位文件，说明如何用真实训练后的模型替换轻量级实现。

## 模块一览

| 模块 | 课程主题 | 任务 | 当前实现 |
|------|---------|------|---------|
| `demand_prediction/` | MLP 回归 | 基于商品特征预测未来 7 天销量 | `LightweightDemandMLP` 确定性回归器 |
| `fraud_detection/` | 二分类 | 将订单风险评分在 0 到 1 之间 | `LightweightFraudClassifier` 逻辑回归风格评分器 |
| `product_category_classifier/` | 监督分类 | 将商品名称映射到分类标签 | 基于关键词的规则分类器 |

## 智能体如何使用这些模块

- `DemandPredictionAgent.predict()` 对购物车中每个商品调用 `predict_demand(product)` 并汇总结果。
- `FraudDetectionAgent.score()` 调用 `predict_risk(features)`，传入订单级别特征。
- 后端目前尚未在主订单流程中调用 `predict_category()`，但该模块已准备好用于商品目录 enrichment 和自动修复。

## 升级路线

每个模块的进化路径如下：

1. 收集真实历史数据（或生成逼真的合成数据集）。
2. 在 `train.py` 中实现模型训练（PyTorch `nn.Module`、scikit-learn `MLPRegressor` 等）。
3. 将训练后的权重保存为文件（如 `.pt`、`.pkl`、`.joblib`）。
4. 更新 `predict.py` 以加载训练权重并执行推理。
5. 导入 `predict.py` 的智能体代码无需修改。
