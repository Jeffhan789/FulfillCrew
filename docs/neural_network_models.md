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

Model: `LightweightDemandMLP`
- Deterministic MLP-shaped regressor
- Weights and bias are hard-coded for MVP inference
- Output is passed through ReLU and a sigmoid-like scaling

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

Model: `LightweightFraudClassifier`
- Logistic-style scorer with the same contract as a future MLP classifier
- Uses sigmoid on a weighted logit of order features

Future upgrade: compare an SVM baseline against an MLP binary classifier.

## Product Category Classification

Input:

- product name (text)

Output:

- category label (electronics, home, fashion, sports, beauty, books)

Model: keyword-based classifier
- Maps keyword overlap to category scores
- Falls back to "electronics" when no keywords match

Future upgrade: replace with a trained bag-of-words, embedding or MLP classifier.

## Testing

All models include unit tests in `tests/test_ml_models.py` covering:

- Valid output ranges and types
- Sensitivity to key input features
- Edge cases (empty inputs, extreme values)
- Classification accuracy for known keyword patterns

---

# 神经网络模型

MVP 使用轻量级确定性模型，具备稳定的推理接口。在收集更大训练数据集之前，这种方式可确保系统可立即运行。

## 需求预测

输入：

- 价格（price）
- 库存量（quantity）
- 评分（rating）
- 品类指示器（category indicator）
- 类型指示器（type indicator）

输出：

- 未来 7 天预测需求

模型：`LightweightDemandMLP`
- 确定性 MLP 形状回归器
- 权重与偏置在 MVP 推理中硬编码
- 输出经过 ReLU 和类 Sigmoid 缩放

未来升级：使用历史销售记录训练真实的 MLP 回归模型。

## 欺诈检测

输入：

- 订单总额（order total）
- 商品数量（number of items）
- 平均商品单价（average item price）
- 新用户标志（new user flag）
- 配送距离（shipping distance）

输出：

- 0 到 1 的风险评分

模型：`LightweightFraudClassifier`
- 逻辑式评分器，与未来的 MLP 分类器保持相同接口
- 对订单特征的加权 logit 使用 Sigmoid 函数

未来升级：对比 SVM 基线与 MLP 二分类器。

## 商品品类分类

输入：

- 商品名称（文本）

输出：

- 品类标签（electronics、home、fashion、sports、beauty、books）

模型：基于关键词的分类器
- 将关键词重叠映射为品类得分
- 无匹配关键词时默认回退到 "electronics"

未来升级：替换为训练好的词袋、词嵌入或 MLP 分类器。

## 测试

所有模型均在 `tests/test_ml_models.py` 中包含单元测试，覆盖：

- 有效输出范围与类型
- 对关键输入特征的敏感度
- 边界情况（空输入、极端值）
- 已知关键词模式的分类准确性
