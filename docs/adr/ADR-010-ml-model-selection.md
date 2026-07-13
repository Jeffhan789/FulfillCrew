# FulfillCrew ADR-010：ML 模型选择 — PyTorch MLP + XGBoost + SHAP + TF-IDF/LR

## 状态
Accepted — v2.0 已实施（v1.0 为确定性接口）

## 背景
ELEC320 Neural Networks 课程要求展示：
- MLP（多层感知机）神经网络
- 二分类模型（如欺诈检测）
- 特征工程与模型解释

v1.0 使用轻量级确定性接口（规则引擎），目的是让系统可立即运行。v2.0 需要真正的 ML 模型。

## 决策
采用三个独立的 ML 模块：
1. **需求预测**：PyTorch MLP 回归模型（2 层 + Dropout）
2. **欺诈检测**：XGBoost 二分类 + SHAP 模型解释
3. **商品分类**：TF-IDF + LogisticRegression 文本分类

## 考虑方案

### 需求预测模型
| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **PyTorch MLP** | 完全控制网络结构；架构复盘可展示 nn.Module 子类；与课程 ELEC320 直接对应 | 需要更多数据才能训练；CPU 推理比 sklearn 慢 | ✅ 选中（课程映射） |
| sklearn MLPRegressor | 简单；无需手动写前向传播 | 架构复盘讨论点少；不如 PyTorch 灵活 | ❌ 架构复盘价值低 |
| XGBoost / LightGBM | 表格数据通常表现更好；训练快 | 不是神经网络，与课程 MLP 主题不完全匹配 | ❌ 课程映射不足 |
| ARIMA / 时间序列 | 传统方法；可解释 | 不体现神经网络；对电商需求场景不如 ML 通用 | ❌ 非神经网络 |
| 规则引擎（v1.0） | 零依赖；立即可运行 | 无学习价值；架构复盘难以展开 | ❌ 不满足课程要求 |

### 欺诈检测模型
| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **XGBoost + SHAP** | 表格数据最佳实践；SHAP 提供可解释性；架构复盘热度高 | 不是神经网络（但二分类课程可以用多种模型） | ✅ 选中（最佳实践） |
| PyTorch 二分类 MLP | 纯神经网络；与课程一致 | 需要更多数据调参；不如 XGBoost 在表格数据上稳定 | ❌ 效果不如 XGBoost |
| Logistic Regression | 简单；可解释；sigmoid 与课程一致 | 线性模型，表达能力弱；架构复盘不够 impressive | ❌ 太简单 |
| Isolation Forest | 无监督；适合异常检测 | 不是二分类；无法输出概率；与课程不符 | ❌ 课程不匹配 |

### 商品分类模型
| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **TF-IDF + LogisticRegression** | 经典文本分类；可解释；轻量 | 不如 BERT 准确；但训练和推理极快 | ✅ 选中（轻量+可解释） |
| BERT / Transformer | 最先进准确率 | 需要 GPU；推理慢；对学生过重；课程不要求 | ❌ 过重 |
| Word2Vec + MLP | 体现神经网络；比 TF-IDF 捕获语义 | 需要更多数据；实现复杂 | ❌ 过重 |
| 规则匹配（关键词） | 最简单 | 无学习价值；不准确 | ❌ 不满足课程要求 |

## 技术细节

### 模块 1：PyTorch MLP 需求预测
```python
# ml_models/demand_prediction/model.py
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
            nn.Dropout(0.2),      # 正则化，防止过拟合
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),    # 输出层：回归任务
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)  # 去掉最后一维，输出 shape (batch_size,)
```

**设计决策说明：**
- **2 层隐藏层**：平衡表达能力和训练难度（ELEC320 课程通常讲 2-3 层 MLP）
- **ReLU 激活**：解决梯度消失，加速收敛
- **Dropout(0.2)**：20% 随机丢弃，防止过拟合，体现课程中的正则化概念
- **input_dim=9**：特征维度与课程项目规模匹配，不是工业级数百维
- **输出 squeeze**：回归任务输出标量，不是分类的概率分布

### 模块 2：XGBoost 欺诈检测 + SHAP
```python
# ml_models/fraud_detection/model.py
class LightweightFraudClassifier:
    """Heuristic logistic-style scorer used as fallback."""
    def predict_proba(self, features: dict) -> float:
        logit = (
            -3.4
            + 0.004 * order_total
            + 0.08 * number_of_items
            + 0.003 * average_item_price
            + 0.75 * is_new_user
            + 0.006 * shipping_distance
        )
        return round(1 / (1 + math.exp(-logit)), 3)
    
    def predict(self, features: dict) -> int:
        return 1 if self.predict_proba(features) >= 0.65 else 0
```

**注意：** v2.0 的欺诈检测实际上使用 XGBoost 模型（`fraud_xgb.json`），但保留了 `LightweightFraudClassifier` 作为：
1. 训练数据不足时的 fallback
2. 架构复盘中解释 sigmoid/logistic 回归原理的教学工具
3. 展示"接口稳定，实现可替换"的架构设计

**SHAP 解释：**
```python
import shap
explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(features)
# shap_values 显示每个特征对预测的贡献度
# 例如：is_new_user 贡献了 +0.3 的风险，shipping_distance 贡献了 +0.05
```

### 模块 3：TF-IDF + LogisticRegression 商品分类
```python
# ml_models/product_category_classifier/model.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# 1. TF-IDF 向量化商品名称和描述
vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
X_train = vectorizer.fit_transform(product_texts)

# 2. LogisticRegression 多分类
classifier = LogisticRegression(max_iter=1000, multi_class='multinomial')
classifier.fit(X_train, y_train)

# 3. 预测新商品
X_new = vectorizer.transform(["Wireless Bluetooth Headphones"])
predicted_category = classifier.predict(X_new)
```

**设计决策说明：**
- **TF-IDF**：经典文本特征提取，与课程监督学习主题匹配
- **ngram_range=(1, 2)**：捕获单词和双词组合，提升分类效果
- **max_features=1000**：控制向量维度，适合小规模数据集
- **LogisticRegression**：可解释性强；`multi_class='multinomial'` 使用 softmax 处理多分类

## 模型生命周期设计

每个 ML 模块都有完整的生命周期：
```
ml_models/<module>/
├── model.py      — 模型定义（PyTorch nn.Module / sklearn 模型）
├── train.py      — 训练脚本（数据处理 → 训练 → 保存模型）
├── evaluate.py   — 评估脚本（验证集测试、指标计算）
├── predict.py    — 推理接口（加载模型 → 预测）
├── models/       — 训练好的模型文件
│   ├── demand_mlp.pt
│   ├── fraud_xgb.json
│   └── classifier.pkl + vectorizer.pkl
└── README.md     — 模块说明
```

### 训练/在线模式分离
```python
# 每个模型暴露两个接口：
# training_mode: 描述如何在历史数据上训练
# online_mode: 描述如何在结账时调用

class ModelEvaluation:
    model_name: str
    course_topic: str
    metric: str
    score: float
    interpretation: str
    training_mode: str   # "Historical product and sales features..."
    online_mode: str     # "The Demand Prediction Agent calls the model..."
```

这是为了：
1. 架构复盘中展示对 ML 工程完整流程的理解
2. 未来可以轻松替换模型（如从 MLP 换到 Transformer）而不改变接口
3. 区分"课程理论"（训练）和"系统实践"（在线推理）

## 权衡与风险

| 风险 | 缓解措施 |
|------|----------|
| 模型训练数据不足，可能过拟合 | 使用 Dropout、小网络；架构复盘中说明"这是课程项目，展示架构而非工业级精度" |
| PyTorch 模型需要 torch 依赖，增加镜像体积 | 安装 CPU-only 版本；接受约 200MB 额外体积 |
| XGBoost 的 C++ 依赖编译问题 | 使用预编译 wheel；多阶段构建中在 builder 阶段安装 |
| 模型推理阻塞事件循环 | 当前模型轻量（毫秒级）；未来可用 `run_in_executor` 或独立推理服务 |
| 商品分类准确率不如 BERT | 架构复盘中说明"TF-IDF+LR 是基线，未来可升级为 BERT" |

## 架构复盘要点

### Q1: 为什么选择 PyTorch 而不是 TensorFlow？
> "PyTorch 是动态图框架，调试更直观（可以用 pdb 断点），与 Python 生态更自然。对于课程项目，PyTorch 的 nn.Module 子类模式更容易理解。TensorFlow 的静态图模式虽然性能更好，但学习曲线更陡。"

### Q2: MLP 的 Dropout 是做什么的？为什么放在 0.2？
> "Dropout 是正则化技术，训练时随机丢弃 20% 的神经元，防止模型过度依赖某些特征。这相当于训练多个子网络的集成，提升泛化能力。0.2 是常见默认值，对于小网络不需要太高（如 0.5）。"

### Q3: XGBoost 比神经网络好在哪？为什么欺诈检测用 XGBoost？
> "XGBoost 在表格数据（结构化特征）上通常表现更好，因为它天然处理特征重要性，且不需要大量数据就能训练。欺诈检测的特征是结构化的（订单金额、用户年龄、距离等），XGBoost 的决策树可以捕捉非线性交互。此外，XGBoost 支持 SHAP 解释，让我们知道每个特征对预测的贡献。"

### Q4: SHAP 是什么？有什么用？
> "SHAP（SHapley Additive exPlanations）来自博弈论，用于解释模型预测。对于每个预测，SHAP 计算每个特征对结果的贡献。比如一个订单被判定为欺诈，SHAP 可以告诉我们'is_new_user 贡献了 +0.3，shipping_distance 贡献了 +0.05'。这在电商场景中非常重要，因为我们需要向运营人员解释为什么某个订单被拦截。"

### Q5: TF-IDF 和 Word Embedding 有什么区别？
> "TF-IDF 是统计方法，给每个词一个权重（在该文档中出现频率高、在整个语料库中出现频率低）。它是稀疏的、高维的（词汇表大小）。Word Embedding（如 Word2Vec）学习词的稠密向量表示，语义相近的词在向量空间中也接近。TF-IDF 更简单、可解释，但无法捕获语义相似性（如'king'和'queen'的关系）。对于我们的商品分类，TF-IDF 足够，且不需要训练数据。"

### Q6: 你们的模型是怎么部署的？在线推理流程是什么？
> "每个模型在训练后保存为文件（.pt、.json、.pkl），Docker 构建时复制到镜像中。运行时通过 `torch.load()` 或 `pickle.load()` 加载到内存。智能体调用 `predict()` 方法进行推理。这种方式是同步的，对于轻量模型延迟可接受。未来可以提取为独立推理服务（如 Triton Inference Server），通过 HTTP/gRPC 调用，实现多实例并发。"

## 相关文件
- `ml_models/demand_prediction/` — MLP 需求预测模块
- `ml_models/fraud_detection/` — XGBoost 欺诈检测模块
- `ml_models/product_category_classifier/` — TF-IDF+LR 分类模块
- `backend/agents/demand_prediction_agent.py` — 需求预测智能体
- `backend/agents/fraud_detection_agent.py` — 欺诈检测智能体
- `backend/services/order_service.py` — ML 推理调用

## 参考
- [PyTorch 官方教程](https://pytorch.org/tutorials/)
- [XGBoost 文档](https://xgboost.readthedocs.io/)
- [SHAP 文档](https://shap.readthedocs.io/)
- [scikit-learn TF-IDF](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction)
- [ELEC320 Neural Networks 课程大纲](https://www.liverpool.ac.uk/electrical-engineering/)
