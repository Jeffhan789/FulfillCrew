# Data Cleaning Pipeline

This folder represents the COMP315 CA1 foundation. It cleans noisy product JSON records before they are used by the frontend, backend, agent system and ML modules.

## Handled Fields

- `id` — preserved or generated as `p-{index}`
- `name` — trimmed and whitespace collapsed
- `price` — currency symbols stripped, validated to a positive float, defaults to 9.99
- `category` — validated against allowed set, defaults to "electronics"
- `type` — normalised or auto-assigned from category defaults
- `quantity` — parsed to non-negative integer, defaults to 0
- `rating` — clamped to [0, 5], defaults to 0
- `image_link` — validated URL or generated Unsplash fallback

## Run

```bash
node data_processing.js raw_products/products.json cleaned_products/products.json
```

## Test

```bash
node tests/test_data_cleaning.js
```

## Design Notes

The pipeline is intentionally simple so students can understand each transformation step. It demonstrates:

- String normalisation and whitespace handling
- Currency parsing with regex
- Enum validation with fallback defaults
- Defensive numeric parsing and clamping
- URL validation and fallback image generation

---

# 数据清洗管道

本文件夹代表 COMP315 CA1 的基础。它清洗含噪声的商品 JSON 记录，供前端、后端、智能体系统和 ML 模块使用。

## 处理的字段

- `id` — 保留或生成 `p-{index}`
- `name` — 去除首尾空格并合并多余空格
- `price` — 去除货币符号，验证为正浮点数，默认 9.99
- `category` — 验证是否在允许集合中，默认 "electronics"
- `type` — 标准化或按品类默认值自动分配
- `quantity` — 解析为非负整数，默认 0
- `rating` — 钳制到 [0, 5] 范围，默认 0
- `image_link` — 验证 URL 或生成 Unsplash 备用图片

## 运行

```bash
node data_processing.js raw_products/products.json cleaned_products/products.json
```

## 测试

```bash
node tests/test_data_cleaning.js
```

## 设计说明

管道有意保持简单，以便学生理解每个转换步骤。它展示了：

- 字符串规范化与空格处理
- 使用正则表达式的货币解析
- 带默认回退的枚举验证
- 防御性数字解析与钳制
- URL 验证与备用图片生成
