# Database Module

This module defines the data models and in-memory product store used by the backend.

> **Note:** The current MVP uses an in-memory product catalog loaded from `data_cleaning/cleaned_products/products.json`. The next upgrade is to replace this with SQLite or PostgreSQL persistence.

## Files

| File | Description |
|------|-------------|
| `models.py` | Pydantic models: `Product`, `BasketItem`, `OrderRequest`, `OrderResponse`, `AgentDecision`, `WarehouseBid`, `CourseMapping`, `ModelEvaluation` |
| `db.py` | Singleton `product_service` instance exported for use across the backend |

## Models

### Product
Represents a cleaned product record with `id`, `name`, `price`, `category`, `type`, `quantity`, `rating` and `image_link`.

### OrderRequest
Represents a checkout request with `user_id`, `items` (list of `BasketItem`), `shipping_distance` and `is_new_user`.

### OrderResponse
Represents the full order result returned to the frontend, including status, warehouse, bids, risk score, demand prediction, decision log, course trace and model evaluations.

### WarehouseBid
Represents a single warehouse bid with `warehouse_id`, `bid`, `workload`, `distance`, `stock_level`, `processing_speed`, `suitability_score` and `reason`.

---

# 数据库模块

本模块定义后端使用的数据模型和内存商品存储。

> **注意：** 当前 MVP 使用从 `data_cleaning/cleaned_products/products.json` 加载的内存商品目录。下一步升级是将其替换为 SQLite 或 PostgreSQL 持久化。

## 文件

| 文件 | 说明 |
|------|------|
| `models.py` | Pydantic 模型：`Product`、`BasketItem`、`OrderRequest`、`OrderResponse`、`AgentDecision`、`WarehouseBid`、`CourseMapping`、`ModelEvaluation` |
| `db.py` | 单例 `product_service` 实例，导出供后端各处使用 |

## 模型

### Product（商品）
代表清洗后的商品记录，包含 `id`、`name`（名称）、`price`（价格）、`category`（品类）、`type`（类型）、`quantity`（数量）、`rating`（评分）和 `image_link`（图片链接）。

### OrderRequest（订单请求）
代表结账请求，包含 `user_id`（用户 ID）、`items`（`BasketItem` 列表）、`shipping_distance`（配送距离）和 `is_new_user`（是否新用户）。

### OrderResponse（订单响应）
代表返回给前端的完整订单结果，包含状态、仓库、竞价、风险分数、需求预测、决策日志、课程追踪和模型评估。

### WarehouseBid（仓库竞价）
代表单个仓库竞价，包含 `warehouse_id`（仓库 ID）、`bid`（竞价值）、`workload`（负载）、`distance`（距离）、`stock_level`（库存水平）、`processing_speed`（处理速度）、`suitability_score`（适配度分数）和 `reason`（原因）。
