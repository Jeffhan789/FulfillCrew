# Product Category Classifier

## Overview

The MVP uses a lightweight keyword-based classifier to demonstrate supervised classification without requiring a labelled training dataset. It is designed to be replaced by a bag-of-words, TF-IDF or embedding-based neural classifier.

## Model: `KeywordClassifier`

A rule-based keyword matcher that tokenises the product name and counts overlaps against predefined keyword sets per category.

### Keyword Dictionary

| Category | Keywords |
|----------|----------|
| `electronics` | `watch`, `headphone`, `wireless`, `smart`, `device`, `audio` |
| `home` | `lamp`, `desk`, `chair`, `kitchen`, `light` |
| `fashion` | `shirt`, `shoe`, `jacket`, `wearable` |
| `sports` | `ball`, `fitness`, `training`, `equipment` |
| `beauty` | `skin`, `cream`, `care` |
| `books` | `book`, `paperback`, `novel` |

### Matching Logic

1. Tokenise the product name into lowercase words.
2. Count how many tokens overlap with each category's keyword set.
3. Select the category with the highest overlap count.
4. If no keywords match, fall back to `electronics`.

### Input

- Product name as a string (e.g., `"Wireless Noise Cancelling Headphones"`)

### Output

- Category label (one of: `electronics`, `home`, `fashion`, `sports`, `beauty`, `books`)

## Inference

```python
from ml_models.product_category_classifier.predict import predict_category

category = predict_category({"name": "Ergonomic Desk Lamp"})
# Returns: "home"
```

## Training Placeholder

```bash
python ml_models/product_category_classifier/train.py
```

The `train.py` script currently prints a placeholder message. To upgrade:

1. Collect a labelled product dataset with `(name, category)` pairs
2. Build a bag-of-words vectoriser or train a word embedding model
3. Train an SVM, MLP or transformer-based classifier
4. Evaluate with accuracy, precision, recall and F1-score per category
5. Replace `classify_category()` with the trained model, keeping the same string input/output interface

---

# 商品品类分类器

## 概览

MVP 使用轻量级基于关键词的分类器来演示监督分类，无需标记训练数据集。它被设计为可被词袋、TF-IDF 或基于嵌入的神经分类器替换。

## 模型：`KeywordClassifier`

一个基于规则的关键词匹配器，将商品名称分词，并与每个品类预定义的关键词集合统计重叠数量。

### 关键词词典

| 品类 | 关键词 |
|------|--------|
| `electronics`（电子） | `watch`、`headphone`、`wireless`、`smart`、`device`、`audio` |
| `home`（家居） | `lamp`、`desk`、`chair`、`kitchen`、`light` |
| `fashion`（时尚） | `shirt`、`shoe`、`jacket`、`wearable` |
| `sports`（运动） | `ball`、`fitness`、`training`、`equipment` |
| `beauty`（美妆） | `skin`、`cream`、`care` |
| `books`（图书） | `book`、`paperback`、`novel` |

### 匹配逻辑

1. 将商品名称分词为小写单词。
2. 统计每个品类的关键词集合有多少词重叠。
3. 选择重叠数量最高的品类。
4. 如果没有关键词匹配，则回退到 `electronics`。

### 输入

- 商品名称字符串（例如 `"Wireless Noise Cancelling Headphones"`）

### 输出

- 品类标签（`electronics`、`home`、`fashion`、`sports`、`beauty`、`books` 之一）

## 推理

```python
from ml_models.product_category_classifier.predict import predict_category

category = predict_category({"name": "Ergonomic Desk Lamp"})
# 返回："home"
```

## 训练占位符

```bash
python ml_models/product_category_classifier/train.py
```

`train.py` 脚本目前打印占位符消息。要升级：

1. 收集标记好的商品数据集，包含 `(name, category)` 对
2. 构建词袋向量化器或训练词嵌入模型
3. 训练 SVM、MLP 或基于 transformer 的分类器
4. 使用每个品类的准确率、精确率、召回率和 F1 分数评估
5. 用训练好的模型替换 `classify_category()`，保持相同的字符串输入/输出接口
