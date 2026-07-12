# Fraud Detection Model

The MVP uses a logistic scorer with the same input/output contract as a future MLP binary classifier.

## Input

- order total
- number of items
- average item price
- is new user (boolean)
- shipping distance

## Output

- `risk_score` from 0 to 1

## Model Architecture

`LightweightFraudClassifier`:
- Logistic regression-style scorer
- Computes a weighted logit from order features
- Applies sigmoid to produce a probability-like score
- Threshold at 0.65 to flag orders for review

## Files

- `model.py` — model class definition
- `predict.py` — inference entry point used by the Fraud Detection Agent
- `train.py` — training placeholder for future model training scripts

## Testing

Tests are in `tests/test_ml_models.py` and cover:

- Valid probability range [0, 1]
- New user risk elevation
- Distance sensitivity
- Extreme order edge cases

---

# 欺诈检测模型

MVP 使用逻辑式评分器，与未来的 MLP 二分类器保持相同的输入/输出接口。

## 输入

- 订单总额（order total）
- 商品数量（number of items）
- 平均商品单价（average item price）
- 是否新用户（is new user，布尔值）
- 配送距离（shipping distance）

## 输出

- `risk_score`（风险评分），范围 0 到 1

## 模型架构

`LightweightFraudClassifier`：
- 逻辑回归式评分器
- 从订单特征计算加权 logit
- 应用 Sigmoid 函数生成概率式评分
- 以 0.65 为阈值标记订单进入审核

## 文件

- `model.py` — 模型类定义
- `predict.py` — 欺诈检测智能体使用的推理入口
- `train.py` — 未来模型训练脚本的占位文件

## 测试

测试位于 `tests/test_ml_models.py`，覆盖：

- 有效概率范围 [0, 1]
- 新用户风险提升
- 距离敏感度
- 极端订单边界情况
