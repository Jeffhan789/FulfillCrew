# 05 机器学习模型深入 —— PyTorch MLP + XGBoost + SHAP + TF-IDF

---

## 1. 三大 ML 模块概览

| 模块 | 课程 | 算法 | 输入 | 输出 | 可解释性 |
|------|------|------|------|------|---------|
| 需求预测 | ELEC320 | PyTorch MLP | 9维商品特征 | 未来7天销量 | 间接（特征重要性） |
| 欺诈检测 | ELEC320 | XGBoost + SHAP | 10维订单特征 | 风险分数 [0,1] | SHAP 值 |
| 商品分类 | ELEC320 | TF-IDF + LogisticRegression | 商品名称文本 | 类别标签 | 关键词匹配 |

---

## 2. 需求预测：PyTorch MLP

### 2.1 网络架构

```python
import torch.nn as nn

class DemandMLP(nn.Module):
    def __init__(self, input_dim: int = 9) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),   # 输入层 → 隐藏层1
            nn.ReLU(),                   # 激活：引入非线性
            nn.Dropout(0.2),             # 正则化：防止过拟合
            nn.Linear(64, 32),          # 隐藏层1 → 隐藏层2
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),           # 隐藏层2 → 输出层
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)  # 去掉最后维度，输出标量
```

**架构复盘表达**："这是一个 3 层全连接网络（输入层-隐藏层1-隐藏层2-输出层），输入 9 维特征，经过 ReLU 激活和 Dropout 正则化，输出未来 7 天销量预测。使用 MSELoss 和 Adam 优化器训练。"

### 2.2 特征工程

```python
feature_vec = [
    price,              # 价格（连续）
    rating,             # 评分（连续）
    category_enc,       # 类别编码（electronics=1.0, home=0.5）
    type_enc,           # 类型编码（device=1.0, audio=0.8, lighting=0.6）
    day_of_week,        # 星期几（0-6）
    month,              # 月份（1-12）
    is_weekend,         # 是否周末（0/1）
    sales_last_7_days,  # 近7天销量
    sales_last_30_days, # 近30天销量
]
```

**关键设计**：类别和类型做了**手动编码**（Manual Encoding），而非 One-hot。因为类别数量少，手动编码保留语义距离（electronics 比 home 更"热销"，编码值更高）。

### 2.3 训练流程

```python
def train():
    # 1. 加载商品目录 + 生成 2000 条合成数据
    products = load_products()
    X, y = generate_synthetic_data(products, n_samples=2000)
    
    # 2. 划分训练集/测试集（80/20）
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # 3. DataLoader 批处理
    train_loader = DataLoader(DemandDataset(X_train, y_train), batch_size=32, shuffle=True)
    
    # 4. 训练循环
    model = DemandMLP(input_dim=9)
    criterion = nn.MSELoss()  # 回归任务：均方误差
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    for epoch in range(1, 51):
        model.train()
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()      # 清空梯度
            outputs = model(batch_x)   # 前向传播
            loss = criterion(outputs, batch_y)  # 计算损失
            loss.backward()            # 反向传播
            optimizer.step()           # 更新权重
```

#### 合成数据生成逻辑

```python
base_demand = (
    50.0
    * math.exp(-price / 100.0)      # 价格敏感度：价格越高，需求越低
    * (1.0 + (rating - 3.0) / 5.0)  # 评分加成
    * (1.0 + 0.1 * math.sin(2 * math.pi * month / 12.0))  # 季节性
    * (1.2 if is_weekend else 1.0)  # 周末加成
    * (1.5 if category == "electronics" else 1.0)  # 品类加成
)
```

**为什么用合成数据**：教学项目没有真实销售历史，合成数据让模型能立即运行。每个样本添加高斯噪声 `random.gauss(0, 3.0)` 防止过拟合。

### 2.4 推理接口

```python
# predict.py
import torch
from ml_models.demand_prediction.model import DemandMLP

def predict_demand(product_features: dict) -> int:
    model = DemandMLP(input_dim=9)
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()  # 关闭 Dropout 和 BatchNorm 的随机性
    
    x = torch.tensor([extract_features(product_features)], dtype=torch.float32)
    with torch.no_grad():  # 推理时不需要计算梯度，节省内存
        prediction = model(x).item()
    
    return max(0, round(prediction))
```

**架构复盘重点**：
- `model.eval()`：关闭训练模式特有的随机性（如 Dropout）
- `torch.no_grad()`：禁用梯度计算，减少内存占用，加速推理
- `map_location="cpu"`：确保模型可在 CPU 环境加载（容器通常无 GPU）

---

## 3. 欺诈检测：XGBoost + SHAP

### 3.1 XGBoost 原理（简述）

XGBoost（eXtreme Gradient Boosting）是梯度提升决策树的优化实现：

```
1. 初始化：F_0(x) = argmin_c Σ L(y_i, c)  # 所有样本的均值
2. 迭代 t = 1..T:
   a. 计算残差（负梯度）：r_i = -∂L(y_i, F_{t-1}(x_i)) / ∂F_{t-1}(x_i)
   b. 拟合回归树 h_t(x) 去预测残差 r_i
   c. 更新：F_t(x) = F_{t-1}(x) + η * h_t(x)  # η 是学习率
3. 输出：F_T(x) = Σ h_t(x)
```

**架构复盘表达**："XGBoost 属于集成学习中的 Boosting 方法，通过串行训练多棵决策树，每棵树拟合前一棵树的残差，逐步减小预测误差。它在 Kaggle 竞赛中长期占据主导地位，因为对小样本、特征混杂的数据集效果极佳。"

### 3.2 特征设计

```python
FEATURE_COLUMNS = [
    "order_total",            # 订单总金额
    "number_of_items",        # 商品数量
    "average_item_price",     # 平均单价
    "is_new_user",            # 是否新用户（0/1）
    "account_age_days",       # 账户年龄
    "shipping_distance",      # 配送距离
    "billing_shipping_match", # 账单地址与配送地址是否一致
    "order_hour",             # 下单时间（小时）
    "is_night_order",         # 是否夜间下单（0/1）
    "orders_in_last_hour",    # 最近1小时下单次数
]
```

### 3.3 SHAP 可解释性

SHAP（SHapley Additive exPlanations）基于博弈论中的 Shapley Value：

```python
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(features)

# shap_values 是一个数组，每个元素表示该特征对预测结果的"贡献度"
# 正值 = 增加风险，负值 = 降低风险
```

**架构复盘表达**："SHAP 值回答了一个核心问题：这个特征的取值让预测结果比基准值高了多少或低了多少？比如 'is_new_user=1' 贡献了 +0.15 的风险分数，说明新用户身份是欺诈风险的重要因素。这让模型从黑盒变成了可解释系统，满足金融场景的合规要求。"

### 3.4 回退机制

```python
class LightweightFraudClassifier:
    def predict_proba(self, features: dict) -> float:
        logit = (
            -3.4
            + 0.004 * order_total
            + 0.08 * number_of_items
            + 0.003 * average_item_price
            + 0.75 * is_new_user
            + 0.006 * shipping_distance
        )
        return round(1 / (1 + math.exp(-logit)), 3)  # Sigmoid
```

这是一个**逻辑回归风格**的启发式评分器。当没有训练好的 XGBoost 模型时自动回退，保证系统始终可用。

---

## 4. 商品分类：TF-IDF + LogisticRegression

### 4.1 关键词匹配回退

```python
KEYWORDS = {
    "electronics": {"watch", "headphone", "wireless", "smart", "device", "audio"},
    "home": {"lamp", "desk", "chair", "kitchen", "light"},
    "fashion": {"shirt", "shoe", "jacket", "wearable"},
    "sports": {"ball", "fitness", "training", "equipment"},
    "beauty": {"skin", "cream", "care"},
    "books": {"book", "paperback", "novel"},
}

def classify_category(name: str) -> str:
    tokens = set(name.lower().split())
    scores = {category: len(tokens & words) for category, words in KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "electronics"
```

### 4.2 训练版：TF-IDF + LogisticRegression

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle

# 训练
vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
X_tfidf = vectorizer.fit_transform(product_names)  # 将文本转为 TF-IDF 向量

clf = LogisticRegression(max_iter=1000, class_weight="balanced")
clf.fit(X_tfidf, labels)

# 保存
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))
pickle.dump(clf, open("classifier.pkl", "wb"))
```

**TF-IDF 原理**：
- **TF** (Term Frequency)：词在文档中出现次数 / 文档总词数
- **IDF** (Inverse Document Frequency)：log(文档总数 / 包含该词的文档数)
- **TF-IDF = TF × IDF**：同时衡量"词在本文档的重要性"和"词在所有文档中的区分度"

**架构复盘表达**："TF-IDF 将文本转为数值向量，高 TF-IDF 值表示该词在该文档中频繁出现、但在整个语料中不常见，因此具有很强的类别区分能力。配合 LogisticRegression（Softmax 多分类），实现轻量级文本分类。"

---

## 5. 模型评估指标

### 5.1 回归任务（需求预测）

| 指标 | 公式 | 解释 |
|------|------|------|
| MSE | 1/n Σ(y_pred - y_true)² | 均方误差，对大误差敏感 |
| MAE | 1/n Σ\|y_pred - y_true\| | 平均绝对误差，直观 |
| MAPE | 1/n Σ\|y_pred - y_true\| / y_true | 百分比误差，便于比较不同量纲 |
| R² | 1 - MSE/Var(y) | 解释方差比例，1 为完美预测 |

### 5.2 分类任务（欺诈检测）

| 指标 | 解释 |
|------|------|
| ROC-AUC | ROC 曲线下面积，0.5 随机，1 完美 |
| PR-AUC | Precision-Recall 曲线下面积，对不平衡数据更敏感 |
| Precision | TP / (TP + FP)，预测为欺诈中有多少是真的 |
| Recall | TP / (TP + FN)，真实欺诈中有多少被检出 |
| F1 | 2 × Precision × Recall / (Precision + Recall) |

**架构复盘表达**："欺诈检测中，Precision 和 Recall 往往此消彼长。提高阈值 → Precision↑, Recall↓（更严格，减少误报）；降低阈值 → Precision↓, Recall↑（更宽松，减少漏报）。业务上需权衡：漏报（真欺诈放行）的成本 vs 误报（正常订单拦截）的客户体验成本。"

---

## 6. 架构复盘高频题

**Q: 为什么需求预测用 MLP 而不是 XGBoost？**

> A: 需求预测是**回归**任务，MLP 能捕捉特征间的非线性交互（如价格 × 评分的耦合效应）。XGBoost 也能做回归，但在特征维度低（9维）、样本量中等（2000条）时，MLP 更轻量，且 PyTorch 框架更便于后续扩展到更复杂的时序模型（如 LSTM、Transformer）。

**Q: Dropout 在推理时为什么关闭？**

> A: Dropout 是训练阶段的正则化技术，随机丢弃部分神经元防止过拟合。推理时需要确定性的输出，所以 `model.eval()` 关闭 Dropout，所有神经元都参与计算。如果推理时保持 Dropout 开启，同一输入每次预测结果不同，不可接受。

**Q: 合成数据和真实数据训练的模型有什么区别？**

> A: 合成数据的分布由生成函数决定，模型学到的模式是"人造的"（如价格敏感度 = exp(-price/100)）。真实数据包含更复杂的噪声、异常值和分布漂移。教学项目中合成数据让系统能立即运行，但生产环境必须用真实历史数据重新训练，并监控模型漂移（Model Drift）。

**Q: 如何处理类别不平衡（欺诈样本远少于正常样本）？**

> A: 几种策略：
> 1. **重采样**：SMOTE 合成少数类样本，或下采样多数类
> 2. **类别权重**：`class_weight="balanced"` 让模型更关注少数类
> 3. **调整阈值**：降低分类阈值提高 Recall（宁可误杀不可放过）
> 4. **代价敏感学习**：给假阴性（漏报欺诈）设置更高损失权重
> 5. **集成方法**：如 XGBoost 的 `scale_pos_weight` 参数

**Q: 如果特征维度从 9 增加到 1000，模型架构要怎么改？**

> A: 
> 1. **降维**：PCA、t-SNE、UMAP 将 1000 维压缩到 50-100 维
> 2. **特征选择**：用 L1 正则化（Lasso）自动筛选重要特征
> 3. **网络加深**：增加隐藏层（如 1000 → 512 → 256 → 128 → 1），配合 BatchNorm 和更激进的 Dropout
> 4. **Embedding**：类别特征用 Embedding Layer（如 electronics → 16 维稠密向量）替代 One-hot
> 5. **注意力机制**：让模型自动学习哪些特征更重要
