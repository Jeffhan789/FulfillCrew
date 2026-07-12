# API Module

This module defines the FastAPI route handlers.

## Routes

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| `products.py` | `/products` | `GET /products` — list all products |
| `orders.py` | `/orders` | `POST /orders` — create a new order |
| `agents.py` | `/agents` | `GET /agents` — list agents<br>`GET /agents/course-map` — course mapping<br>`GET /agents/model-evaluations` — model evaluations |

All routers are registered in `backend/main.py`.

---

# API 模块

本模块定义 FastAPI 路由处理器。

## 路由

| 路由 | 前缀 | 端点 |
|------|------|------|
| `products.py` | `/products` | `GET /products` — 列出所有商品 |
| `orders.py` | `/orders` | `POST /orders` — 创建新订单 |
| `agents.py` | `/agents` | `GET /agents` — 列出智能体<br>`GET /agents/course-map` — 课程映射<br>`GET /agents/model-evaluations` — 模型评估 |

所有路由在 `backend/main.py` 中注册。
