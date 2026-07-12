# Demand Prediction Model

First MVP version exposes an inference function shaped like an MLP regression model output. It can be replaced by a trained PyTorch, TensorFlow or scikit-learn MLP later.

## Input Features

- price
- quantity
- rating
- category
- type
- previous sales features (placeholder for future trained models)

## Output

- predicted sales for the next 7 days

## Model Architecture

`LightweightDemandMLP`:
- Single linear layer with hard-coded weights and bias
- ReLU activation (`max(0, activation)`)
- Output scaled through a sigmoid-like function
- Final result rounded to nearest integer with a minimum of 1

## Files

- `model.py` — model class definition
- `predict.py` — inference entry point used by the Demand Prediction Agent
- `train.py` — training placeholder for future model training scripts

## Testing

Tests are in `tests/test_ml_models.py` and cover:

- Positive integer output guarantee
- Feature sensitivity
- Category and type boost effects
- Empty input handling

---

# 需求预测模型

MVP 第一版暴露的推理函数接口与 MLP 回归模型输出一致。后续可替换为训练好的 PyTorch、TensorFlow 或 scikit-learn MLP。

## 输入特征

- 价格（price）
- 库存量（quantity）
- 评分（rating）
- 品类（category）
- 类型（type）
- 历史销量特征（未来训练模型的占位符）

## 输出

- 未来 7 天预测销量

## 模型架构

`LightweightDemandMLP`：
- 单一线性层，硬编码权重与偏置
- ReLU 激活（`max(0, activation)`）
- 输出通过类 Sigmoid 函数缩放
- 最终结果四舍五入为整数，最小值为 1

## 文件

- `model.py` — 模型类定义
- `predict.py` — 需求预测智能体使用的推理入口
- `train.py` — 未来模型训练脚本的占位文件

## 测试

测试位于 `tests/test_ml_models.py`，覆盖：

- 正整数输出保证
- 特征敏感度
- 品类与类型加成效果
- 空输入处理
