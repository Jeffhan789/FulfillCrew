# Testing Guide

This document explains how to run the full test suite for FulfillCrew.

## Quick Start

Run everything:

```bash
# Backend (Python)
pytest tests/ -v

# Frontend (TypeScript)
cd frontend && npm test

# Data cleaning (Node.js)
node tests/test_data_cleaning.js
```

## Backend Tests (`tests/`)

| File | Coverage |
|------|----------|
| `test_agents.py` | Order workflow, fraud decisions, stock rejection, warehouse bids, course trace, model evaluations |
| `test_ml_models.py` | Demand MLP, fraud classifier, category classifier — ranges, sensitivity, edge cases |
| `test_api.py` | FastAPI endpoints — health, products, orders, agents, CORS, validation |
| `test_services.py` | Product service, order service — totals, stock reservation, UUID generation |
| `conftest.py` | Shared fixtures for products, services and order requests |

### Run with coverage

```bash
pytest tests/ --cov=backend --cov=ml_models --cov-report=term-missing
```

## Frontend Tests (`frontend/src/*.test.ts`)

Frontend tests use Vitest with jsdom environment. They cover:

- Basket total calculation
- Product filtering by search query
- In-stock filter logic
- Sorting by price and rating
- Data cleaning helper logic

### Run in watch mode

```bash
cd frontend
npm run test:watch
```

## Data Cleaning Tests (`tests/test_data_cleaning.js`)

Node.js assertions validating the `cleanProduct` transformations:

- Name trimming and whitespace collapse
- Price parsing with currency symbols
- Category fallback to "electronics"
- Negative quantity clamped to 0
- Rating clamped to [0, 5]

## CI Pipeline

GitHub Actions (`.github/workflows/ci.yml`) runs all tests automatically on every push and pull request:

1. **Backend Tests** — Python 3.12, pytest
2. **Frontend Tests & Build** — Node 20, Vitest, TypeScript build
3. **Data Cleaning** — Node.js pipeline verification
4. **Docker Build** — Image build check

---

# 测试指南

本文档说明如何运行 FulfillCrew 的完整测试套件。

## 快速开始

运行全部测试：

```bash
# 后端（Python）
pytest tests/ -v

# 前端（TypeScript）
cd frontend && npm test

# 数据清洗（Node.js）
node tests/test_data_cleaning.js
```

## 后端测试（`tests/`）

| 文件 | 覆盖范围 |
|------|----------|
| `test_agents.py` | 订单工作流、欺诈决策、库存拒绝、仓储竞价、课程轨迹、模型评估 |
| `test_ml_models.py` | 需求预测 MLP、欺诈分类器、品类分类器 — 范围、敏感度、边界情况 |
| `test_api.py` | FastAPI 端点 — 健康检查、商品、订单、智能体、CORS、验证 |
| `test_services.py` | 商品服务、订单服务 — 总额、库存预留、UUID 生成 |
| `conftest.py` | 商品、服务与订单请求的共享 fixture |

### 带覆盖率运行

```bash
pytest tests/ --cov=backend --cov=ml_models --cov-report=term-missing
```

## 前端测试（`frontend/src/*.test.ts`）

前端测试使用 Vitest 配合 jsdom 环境。覆盖：

- 购物篮总额计算
- 按搜索词过滤商品
- 库存筛选逻辑
- 按价格和评分排序
- 数据清洗辅助逻辑

### 监视模式运行

```bash
cd frontend
npm run test:watch
```

## 数据清洗测试（`tests/test_data_cleaning.js`）

Node.js 断言，验证 `cleanProduct` 转换：

- 名称去除首尾空格并合并多余空格
- 带货币符号的价格解析
- 品类默认回退到 "electronics"
- 负数量钳制为 0
- 评分钳制到 [0, 5]

## CI 流水线

GitHub Actions（`.github/workflows/ci.yml`）在每次 push 和 pull request 时自动运行所有测试：

1. **后端测试** — Python 3.12，pytest
2. **前端测试与构建** — Node 20，Vitest，TypeScript 构建
3. **数据清洗** — Node.js 管道验证
4. **Docker 构建** — 镜像构建检查
