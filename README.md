# FulfillCrew（智仓通）

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-24+-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.5-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.1-EB622B?logo=xgboost)](https://xgboost.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

> English first. 中文版见后文。

[English](#english) | [中文](#中文)

## English

> **Multi-Agent Order Fulfillment System**
>
> An interview-ready AI + multi-agent e-commerce project built from a clear product idea: turn a simple coursework e-commerce prototype into a full order intelligence system.

## For Students

This repository is designed to be useful for undergraduate students who want a project that is bigger than a normal CRUD app, but still understandable enough to rebuild and explain in interviews.

You can use it as:

- A portfolio project template for AI, cloud and software engineering interviews
- A reference structure for turning coursework into a serious GitHub project
- A starting point for learning FastAPI, React, multi-agent workflows and ML inference APIs
- A base project to fork, extend and compare against your own university modules

If this helps you plan your own final-year project or interview portfolio, a star would be genuinely appreciated.

## Why This Project Exists

Most beginner e-commerce projects stop at product cards and a shopping basket. This project goes further: after checkout, the order is handled by a multi-agent fulfilment workflow and enriched with AI-style prediction results.

The concept and system direction are designed around three university modules:

- **Cloud Computing (COMP315):** Data cleaning, frontend, backend APIs and containerised deployment
- **Multi-Agent Systems (COMP310):** Autonomous order, inventory, coordinator and warehouse agents
- **Neural Networks (ELEC320):** Demand prediction, fraud scoring and category classification

The goal is not just to build another shop UI, but to show how a small coursework foundation can grow into a realistic engineering portfolio project.

## What It Demonstrates

- A JavaScript product data cleaning pipeline for noisy e-commerce records
- A React shopping interface with search, sorting, in-stock filtering and basket checkout
- A FastAPI backend exposing product, order and agent endpoints
- A simplified Contract Net Protocol for warehouse bidding
- Demand prediction and fraud detection modules with stable inference interfaces
- Docker-ready multi-service architecture with Nginx reverse proxy
- A course intelligence dashboard showing how COMP315, COMP310 and ELEC320 map into the running system

## Why It Is Star-Worthy

This project is intentionally built as a learning bridge: simple enough for students to read, but structured enough to discuss with interviewers.

- It connects frontend, backend, agents and ML in one coherent flow.
- It shows how to upgrade coursework instead of abandoning it after submission.
- It keeps the first version runnable, then leaves clear upgrade paths for stronger models and deployment.
- It documents both the engineering structure and the thinking behind the project.

## System Architecture

```text
Browser (User)
       |
       v
Nginx (frontend container)
  • Serves React SPA static assets
  • Proxies /api/* -> backend:8000
  • Proxies /health, /docs, /openapi.json -> backend:8000
       |
       | Docker network: fulfillcrew-network
       v
FastAPI (backend container)
  • /products     -- list products
  • /orders       -- create order (triggers agent workflow)
  • /agents       -- list agents, course map, model evals
  • /health       -- health check
       |
  +----+----+----+
  |    |    |    |
Order  Inventory Coordinator Demand + Fraud
Agent  Agent      Agent (bids) Agents (ML)
```

## Project Structure

```text
├── data_cleaning/          Product data cleaning pipeline (Node.js)
│   ├── data_processing.js
│   ├── raw_products/
│   └── cleaned_products/
├── frontend/               React + Vite + TypeScript SPA
│   ├── src/main.tsx
│   ├── nginx.conf          Nginx reverse proxy config
│   └── Dockerfile          Multi-stage frontend build
├── backend/                FastAPI backend & multi-agent workflow
│   ├── main.py             FastAPI app entrypoint
│   ├── api/                API routers (products, orders, agents)
│   ├── agents/             Multi-agent implementations
│   ├── services/           Business logic services
│   ├── database/           Pydantic models & in-memory DB
│   └── requirements.txt
├── ml_models/              Lightweight ML inference modules
│   ├── demand_prediction/
│   ├── fraud_detection/
│   └── product_category_classifier/
├── tests/                  Smoke tests (pytest + Node.js)
├── docs/                   Design notes & Chinese project explanation
├── Dockerfile              Backend multi-stage Dockerfile
├── docker-compose.yml      Production orchestration
├── docker-compose.dev.yml  Development orchestration (hot reload)
├── .env.example            Environment variable template
├── .dockerignore           Docker build context exclusions
└── README.md               This file
```

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Lucide React |
| Backend | Python 3.12, FastAPI, Uvicorn, Pydantic |
| Agents | Python classes with Contract Net Protocol bidding |
| ML | Deterministic lightweight interfaces (upgradeable to MLP/SVM) |
| Data Cleaning | Node.js native (fs, path) |
| Testing | pytest, Node.js assertions |
| Containerisation | Docker, Docker Compose, Nginx |

## Quick Start -- Docker (Recommended)

The fastest way to run the full system is with Docker Compose.

### Prerequisites

- Docker Engine >= 24.0
- Docker Compose >= 2.20

### Production Mode

```bash
# 1. Clone the repository and navigate into it
cd FulfillCrew

# 2. (Optional) copy environment template
cp .env.example .env

# 3. Build and start all services
docker compose up --build -d

# 4. Verify services are healthy
docker compose ps

# 5. Open the frontend
open http://localhost        # macOS
# or
xdg-open http://localhost    # Linux
```

Services:

- **Frontend** -> http://localhost (Nginx serving React SPA)
- **Backend API** -> http://localhost:8000
- **API Docs (Swagger UI)** -> http://localhost:8000/docs
- **OpenAPI Schema** -> http://localhost:8000/openapi.json

### Stop Production Services

```bash
docker compose down
```

To remove volumes and images as well:

```bash
docker compose down --volumes --rmi all
```

## Development Mode

For local development with hot reload on the backend:

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

- **Frontend (dev)** -> http://localhost:8080
- **Backend (dev, hot reload)** -> http://localhost:8000

The backend container mounts `./backend`, `./ml_models` and `./data_cleaning/cleaned_products` as read-only volumes so code changes are reflected immediately without rebuilding the image.

## Manual Development (Without Docker)

If you prefer to run services directly on your machine:

### 1. Clean Sample Product Data

```bash
node data_cleaning/data_processing.js \
  data_cleaning/raw_products/products.json \
  data_cleaning/cleaned_products/products.json
```

### 2. Run Backend

```bash
python3 -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### 3. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server (Vite) proxies `/api` and `/health` requests to the backend automatically. You only need to open http://localhost:5173.

## API Examples

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

Response:
```json
{"status": "ok"}
```

### List Products

```bash
curl http://127.0.0.1:8000/products
```

### Create an Order

```bash
curl -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user",
    "items": [{"product_id": "p-1001", "quantity": 1}],
    "shipping_distance": 18,
    "is_new_user": true
  }'
```

Example response includes:

- `order_status` -- created, review_required or rejected_out_of_stock
- `selected_warehouse` -- best bid winner
- `risk_score` -- 0-1 fraud probability
- `fraud_status` -- approved or review_required
- `predicted_demand_next_7_days` -- integer forecast
- `restock_recommendation` -- restock guidance
- `bids` -- full warehouse bid list with explainable reasons
- `decision_log` -- step-by-step agent reasoning
- `course_trace` -- module mapping evidence
- `model_evaluations` -- ML interface metrics and interpretation

### Agent List

```bash
curl http://127.0.0.1:8000/agents
```

### Course Map

```bash
curl http://127.0.0.1:8000/agents/course-map
```

### Model Evaluations

```bash
curl http://127.0.0.1:8000/agents/model-evaluations
```

## Demo Flow

1. Raw product JSON is cleaned into stable product records by the data cleaning pipeline.
2. The frontend loads products from the backend API (`GET /products`).
3. A user searches, sorts, filters and adds products to the basket.
4. Checkout sends the basket to the backend order API (`POST /orders`).
5. **Order Agent** receives the order and starts the fulfilment workflow.
6. **Fraud Detection Agent** returns a risk score; high scores trigger review.
7. **Inventory Agent** checks stock availability for every line item.
8. **Coordinator Agent** announces the fulfilment task to all Warehouse Agents.
9. **Warehouse Agents** bid using workload, stock level, distance and processing speed; each bid includes an explainable reason.
10. The best warehouse is selected using the lowest-bid policy.
11. **Demand Prediction Agent** estimates the next 7-day demand for the selected products.
12. The frontend displays the order status, selected warehouse, risk score, predicted demand, warehouse bids, model evidence and the full decision log.

## Agent Layer

The order workflow is intentionally modelled as a multi-agent system rather than a single service function.

| Agent | Role |
|-------|------|
| Order Agent | Receives the checkout request and starts the fulfilment workflow. |
| Fraud Detection Agent | Scores the order and decides whether review is required. |
| Inventory Agent | Checks stock and reserves inventory after approval. |
| Coordinator Agent | Announces the fulfilment task and selects the best warehouse bid. |
| Warehouse Agents | Bid using workload, stock level, distance and processing speed; return explainable bid reasons. |
| Demand Prediction Agent | Estimates future demand and provides restock guidance. |

## AI / ML Layer

The first version uses lightweight deterministic model interfaces so the whole system can run immediately. These interfaces are designed to be replaced later by trained MLP, SVM or PyTorch models.

| Module | Course Topic | Input -> Output |
|--------|-------------|----------------|
| Demand Prediction | MLP regression | Product features -> predicted next 7-day sales |
| Fraud Detection | Binary classification | Order features -> risk score from 0 to 1 |
| Category Classification | Supervised classification | Product text and metadata -> category labels |

Each model interface exposes a `training_mode` description (how it would be trained on historical data) and an `online_mode` description (how it is called during checkout). This makes it easy to swap in real trained models later without changing the agent contracts.

## Testing

### Python (Backend + Agents)

```bash
pytest tests/test_agents.py -v
```

### JavaScript (Data Cleaning)

```bash
node tests/test_data_cleaning.js
```

### Docker Health Checks

Both the frontend and backend containers declare Docker health checks. You can inspect them with:

```bash
docker compose ps
docker inspect --format='{{.State.Health.Status}}' fulfillcrew-backend
docker inspect --format='{{.State.Health.Status}}' fulfillcrew-frontend
```

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed.

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_LOG_LEVEL` | FastAPI log level | `info` |
| `BACKEND_PORT` | The port the FastAPI backend listens on inside the container | `8000` |
| `FRONTEND_PORT` | The port the Nginx frontend listens on (host mapping) | `80` |
| `API_BASE_URL` | The base URL used by the frontend to reach the backend | `http://127.0.0.1:8000` |
| `CORS_ORIGINS` | Comma-separated list of allowed CORS origins | See `.env.example` |

## Roadmap

- Replace lightweight prediction modules with trained MLP/SVM models
- Add SQLite or PostgreSQL persistence for products, orders and agent logs
- Add dashboard charts for warehouse bids and demand forecasts
- Add screenshots and a short demo GIF for GitHub showcase
- Deploy to a cloud VM or Kubernetes cluster
- Add CI/CD pipeline (GitHub Actions) for test + build + push
- Add structured logging and observability (Prometheus + Grafana)
- Implement real-time WebSocket updates for order status

## Portfolio Summary

Extended a coursework-based React e-commerce prototype into an AI-powered multi-agent fulfilment system with backend APIs, autonomous agent coordination, explainable warehouse bidding, prediction modules, course mapping dashboards and Docker-ready deployment with Nginx reverse proxy.

---

## 中文

> **FulfillCrew（智仓通）**
>
> 一个面向面试展示的 AI + 多智能体电商项目。核心理念：将一个简单的课程作业电商原型，工程化升级为一个完整的订单智能履约系统。

## 面向学生

本仓库专为本科生设计，适合那些想要一个比传统 CRUD 应用更有深度、但又在面试中能够讲清楚、重建出来的项目。

你可以将它用作：

- AI、云计算和软件工程面试的作品集项目模板
- 将课程作业转化为严肃 GitHub 项目的参考结构
- 学习 FastAPI、React、多智能体工作流和 ML 推理接口的入门项目
- 一个可以 fork、扩展并与自己大学课程对比的基础项目

如果这个项目对你规划毕业设计或面试作品集有帮助，欢迎点个 star，真心感谢。

## 项目初衷

大多数入门级电商项目止步于商品卡片和购物车。本项目走得更远：结账之后，订单会进入一个多智能体履约工作流，并用 AI 风格的预测结果进行 enrich。

概念和系统方向围绕三门大学课程设计：

- **云计算（COMP315）：** 数据清洗、前端、后端 API 与容器化部署
- **多智能体系统（COMP310）：** 自主订单、库存、协调与仓库智能体
- **神经网络（ELEC320）：** 需求预测、欺诈评分与商品分类

目标不是再建一个普通商店界面，而是展示如何将一个课程作业基础工程化，成长为真实可用的工程项目作品集。

## 项目展示能力

- JavaScript 商品数据清洗管道，处理噪声电商记录
- React 购物界面，支持搜索、排序、库存过滤、购物篮与结账
- FastAPI 后端，暴露商品、订单与智能体端点
- 简化版合同网协议（Contract Net Protocol）用于仓库竞价
- 需求预测与欺诈检测模块，具备稳定的推理接口
- 基于 Docker 的多服务架构，配 Nginx 反向代理
- 课程智能仪表盘，展示 COMP315、COMP310 和 ELEC320 如何映射到运行系统中

## 为什么值得 Star

本项目刻意设计为一座学习桥梁：简单到学生能读懂，又结构化到足以在面试中深入讨论。

- 前端、后端、智能体与 ML 在一条连贯流程中衔接
- 展示如何升级课程作业，而不是提交后就抛弃
- 第一版本可立即运行，同时留下清晰的升级路径到更强模型和真实部署
- 同时记录工程结构本身和项目背后的设计思路

## 系统架构

```text
浏览器（用户）
       |
       v
Nginx（前端容器）
  • 提供 React SPA 静态资源
  • 代理 /api/* -> backend:8000
  • 代理 /health、/docs、/openapi.json -> backend:8000
       |
       | Docker 网络: fulfillcrew-network
       v
FastAPI（后端容器）
  • /products     -- 商品列表
  • /orders       -- 创建订单（触发智能体工作流）
  • /agents       -- 智能体列表、课程映射、模型评估
  • /health       -- 健康检查
       |
  +----+----+----+
  |    |    |    |
订单  库存   协调   需求 + 欺诈
智能体 智能体  智能体（竞价）智能体 (ML)
```

## 项目结构

```text
├── data_cleaning/          商品数据清洗管道（Node.js）
│   ├── data_processing.js
│   ├── raw_products/
│   └── cleaned_products/
├── frontend/               React + Vite + TypeScript 单页应用
│   ├── src/main.tsx
│   ├── nginx.conf          Nginx 反向代理配置
│   └── Dockerfile          多阶段前端构建
├── backend/                FastAPI 后端与多智能体工作流
│   ├── main.py             FastAPI 应用入口
│   ├── api/                API 路由（商品、订单、智能体）
│   ├── agents/             多智能体实现
│   ├── services/           业务逻辑服务层
│   ├── database/           Pydantic 模型与内存数据库
│   └── requirements.txt
├── ml_models/              轻量级 ML 推理模块
│   ├── demand_prediction/
│   ├── fraud_detection/
│   └── product_category_classifier/
├── tests/                  冒烟测试（pytest + Node.js）
├── docs/                   设计文档与中文项目说明
├── Dockerfile              后端多阶段 Dockerfile
├── docker-compose.yml      生产环境编排
├── docker-compose.dev.yml  开发环境编排（热重载）
├── .env.example            环境变量模板
├── .dockerignore           Docker 构建上下文排除文件
└── README.md               本文件
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18, TypeScript, Vite, Lucide React |
| 后端 | Python 3.12, FastAPI, Uvicorn, Pydantic |
| 智能体 | Python 类，合同网协议竞价 |
| 机器学习 | 确定性轻量级接口（可升级至 MLP/SVM） |
| 数据清洗 | Node.js 原生模块 (fs, path) |
| 测试 | pytest, Node.js 断言 |
| 容器化 | Docker, Docker Compose, Nginx |

## 快速启动 -- Docker（推荐）

运行完整系统的最快方式是使用 Docker Compose。

### 前置条件

- Docker Engine >= 24.0
- Docker Compose >= 2.20

### 生产模式

```bash
# 1. 克隆仓库并进入目录
cd FulfillCrew

# 2. （可选）复制环境变量模板
cp .env.example .env

# 3. 构建并启动所有服务
docker compose up --build -d

# 4. 验证服务健康状态
docker compose ps

# 5. 打开前端
open http://localhost        # macOS
# 或
xdg-open http://localhost    # Linux
```

服务地址：

- **前端** -> http://localhost（Nginx 提供 React SPA）
- **后端 API** -> http://localhost:8000
- **API 文档（Swagger UI）** -> http://localhost:8000/docs
- **OpenAPI 模式** -> http://localhost:8000/openapi.json

### 停止生产服务

```bash
docker compose down
```

同时移除卷和镜像：

```bash
docker compose down --volumes --rmi all
```

## 开发模式

用于本地开发，后端支持热重载：

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

- **前端（开发版）** -> http://localhost:8080
- **后端（开发版，热重载）** -> http://localhost:8000

后端容器将 `./backend`、`./ml_models` 和 `./data_cleaning/cleaned_products` 以只读卷挂载，代码修改无需重建镜像即可立即生效。

## 手动开发（不借助 Docker）

如果你倾向于直接在本地运行服务：

### 1. 清洗示例商品数据

```bash
node data_cleaning/data_processing.js \
  data_cleaning/raw_products/products.json \
  data_cleaning/cleaned_products/products.json
```

### 2. 运行后端

```bash
python3 -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### 3. 运行前端

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器（Vite）会自动将 `/api` 和 `/health` 请求代理到后端。你只需要打开 http://localhost:5173。

## API 示例

### 健康检查

```bash
curl http://127.0.0.1:8000/health
```

响应：
```json
{"status": "ok"}
```

### 商品列表

```bash
curl http://127.0.0.1:8000/products
```

### 创建订单

```bash
curl -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user",
    "items": [{"product_id": "p-1001", "quantity": 1}],
    "shipping_distance": 18,
    "is_new_user": true
  }'
```

响应示例包含：

- `order_status` -- created、review_required 或 rejected_out_of_stock
- `selected_warehouse` -- 最佳竞价胜出者
- `risk_score` -- 0-1 的欺诈概率
- `fraud_status` -- approved 或 review_required
- `predicted_demand_next_7_days` -- 整数预测值
- `restock_recommendation` -- 补货建议
- `bids` -- 完整仓库竞价列表，附带可解释原因
- `decision_log` -- 逐步智能体推理日志
- `course_trace` -- 课程映射证据
- `model_evaluations` -- ML 接口指标与解释

### 智能体列表

```bash
curl http://127.0.0.1:8000/agents
```

### 课程映射

```bash
curl http://127.0.0.1:8000/agents/course-map
```

### 模型评估

```bash
curl http://127.0.0.1:8000/agents/model-evaluations
```

## 演示流程

1. 原始商品 JSON 通过数据清洗管道转换为稳定商品记录。
2. 前端从后端 API（`GET /products`）加载商品。
3. 用户搜索、排序、过滤并将商品加入购物篮。
4. 结账将购物篮发送至后端订单 API（`POST /orders`）。
5. **订单智能体**接收订单并启动履约工作流。
6. **欺诈检测智能体**返回风险评分；高评分触发人工审核。
7. **库存智能体**检查每个商品行的库存可用性。
8. **协调智能体**向所有仓库智能体发布履约任务。
9. **仓库智能体**基于工作量、库存水平、距离和处理速度进行竞价；每条竞价都附带可解释原因。
10. 使用最低竞价策略选出最佳仓库。
11. **需求预测智能体**估算所选商品未来 7 天需求。
12. 前端展示订单状态、选中仓库、风险评分、预测需求、仓库竞价、模型证据和完整决策日志。

## 智能体层

订单工作流被刻意设计为多智能体系统，而非单一服务函数。

| 智能体 | 角色 |
|--------|------|
| 订单智能体 | 接收结账请求并启动履约工作流 |
| 欺诈检测智能体 | 对订单评分并决定是否需人工审核 |
| 库存智能体 | 检查库存并在审核通过后预留库存 |
| 协调智能体 | 发布履约任务并选择最佳仓库竞价 |
| 仓库智能体 | 基于工作量、库存、距离和速度竞价；返回可解释竞价原因 |
| 需求预测智能体 | 估算未来需求并提供补货建议 |

## AI / ML 层

第一版使用确定性轻量级模型接口，使系统可立即运行。这些接口被设计为后续可被训练好的 MLP、SVM 或 PyTorch 模型替换。

| 模块 | 课程主题 | 输入 -> 输出 |
|------|---------|------------|
| 需求预测 | MLP 回归 | 商品特征 -> 预测未来 7 天销量 |
| 欺诈检测 | 二分类 | 订单特征 -> 0 到 1 的风险评分 |
| 商品分类 | 监督分类 | 商品文本与元数据 -> 类别标签 |

每个模型接口都暴露 `training_mode` 描述（如何在历史数据上训练）和 `online_mode` 描述（结账时如何调用）。这使得后续在不变更智能体契约的情况下，轻松替换为真实训练模型。

## 测试

### Python（后端 + 智能体）

```bash
pytest tests/test_agents.py -v
```

### JavaScript（数据清洗）

```bash
node tests/test_data_cleaning.js
```

### Docker 健康检查

前端和后端容器均声明了 Docker 健康检查。你可以通过以下命令查看：

```bash
docker compose ps
docker inspect --format='{{.State.Health.Status}}' fulfillcrew-backend
docker inspect --format='{{.State.Health.Status}}' fulfillcrew-frontend
```

## 环境变量

复制 `.env.example` 为 `.env` 并按需调整。

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BACKEND_LOG_LEVEL` | FastAPI 日志级别 | `info` |
| `BACKEND_PORT` | 后端容器内部端口 | `8000` |
| `FRONTEND_PORT` | 映射到 Nginx 的主机端口 | `80` |
| `API_BASE_URL` | 前端开发 API 基础 URL（本地非 Docker） | `http://127.0.0.1:8000` |
| `CORS_ORIGINS` | 逗号分隔的允许来源 | 见 `.env.example` |

## 路线图

- 用训练好的 MLP/SVM 模型替换轻量级预测模块
- 添加 SQLite 或 PostgreSQL 持久化，存储商品、订单和智能体日志
- 为仓库竞价和需求预测添加仪表盘图表
- 添加截图和简短演示 GIF 用于 GitHub 展示
- 部署到云服务器或 Kubernetes 集群
- 添加 CI/CD 流水线（GitHub Actions）实现测试 + 构建 + 推送
- 添加结构化日志和可观测性（Prometheus + Grafana）
- 实现订单状态的实时 WebSocket 更新

## 作品集总结

将一个基于课程作业的 React 电商原型，扩展为一个 AI 驱动的多智能体履约系统，包含后端 API、自主智能体协调、可解释仓库竞价、预测模块、课程映射仪表盘，以及基于 Nginx 反向代理的 Docker 就绪部署架构。
