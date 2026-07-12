# Backend

This folder contains the FastAPI backend and the multi-agent order fulfilment workflow. It serves REST APIs to the React frontend and coordinates autonomous agents to process checkout orders.

## Structure

```text
backend/
  api/          — FastAPI routers (products, orders, agents)
  agents/       — Multi-agent system (Order, Inventory, Coordinator, Warehouse, Fraud, Demand)
  database/     — Database models and connection helpers (in-memory for MVP)
  services/     — Business logic services (order service, product service)
  main.py       — FastAPI application entry point
  requirements.txt — Python dependencies
```

## API Routers

- `GET /products` — list cleaned products with search and filtering
- `POST /orders` — create an order and trigger the multi-agent fulfilment workflow
- `GET /health` — health check endpoint
- `GET /agents/course-mapping` — expose course-to-component mapping for the dashboard

## Multi-Agent Workflow

When a `POST /orders` request arrives:

1. Order Agent validates the request payload.
2. Fraud Detection Agent scores the order risk.
3. Inventory Agent checks stock availability for every line item.
4. Coordinator Agent announces the task to Warehouse Agents.
5. Warehouse Agents submit bids with explainable reasoning.
6. Coordinator Agent selects the best warehouse bid.
7. Demand Prediction Agent estimates next 7-day demand for the ordered products.
8. The enriched result is returned to the frontend.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

---

# 后端

本文件夹包含 FastAPI 后端和多智能体订单履约工作流。它向 React 前端提供 REST API，并协调自主智能体来处理结账订单。

## 结构

```text
backend/
  api/          — FastAPI 路由（商品、订单、智能体）
  agents/       — 多智能体系统（订单、库存、协调、仓库、欺诈、需求）
  database/     — 数据库模型和连接助手（MVP 中使用内存存储）
  services/     — 业务逻辑服务（订单服务、商品服务）
  main.py       — FastAPI 应用入口点
  requirements.txt — Python 依赖
```

## API 路由

- `GET /products` — 列出支持搜索和筛选的清洗后商品
- `POST /orders` — 创建订单并触发多智能体履约工作流
- `GET /health` — 健康检查端点
- `GET /agents/course-mapping` — 为仪表盘暴露课程到组件的映射

## 多智能体工作流

当 `POST /orders` 请求到达时：

1. 订单智能体（Order Agent）验证请求载荷。
2. 欺诈检测智能体（Fraud Detection Agent）对订单风险进行评分。
3. 库存智能体（Inventory Agent）检查每件商品的库存可用性。
4. 协调智能体（Coordinator Agent）向仓库智能体发布任务。
5. 仓库智能体（Warehouse Agents）提交附带可解释推理的竞价。
6. 协调智能体（Coordinator Agent）选择最优仓库竞价。
7. 需求预测智能体（Demand Prediction Agent）对订单商品估算未来 7 天需求。
8. 将 enriched 结果返回给前端。

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```
