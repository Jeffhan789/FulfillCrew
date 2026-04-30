# Cloud-Based Multi-Agent E-Commerce Intelligence System

An interview-ready AI + multi-agent e-commerce project built from a clear product idea: turn a simple coursework e-commerce prototype into a full order intelligence system.

中文名：云端多智能体智能电商系统

Chinese readers: this README includes a Chinese project introduction near the end. A longer Chinese overview is also available in [docs/中文项目介绍.md](docs/中文项目介绍.md).

## For Students

This repository is designed to be useful for undergraduate students who want a project that is bigger than a normal CRUD app, but still understandable enough to rebuild and explain in interviews.

You can use it as:

- a portfolio project template for AI, cloud and software engineering interviews
- a reference structure for turning coursework into a serious GitHub project
- a starting point for learning FastAPI, React, multi-agent workflows and ML inference APIs
- a base project to fork, extend and compare against your own university modules

If this helps you plan your own final-year project or interview portfolio, a star would be genuinely appreciated.

## Why This Project Exists

Most beginner e-commerce projects stop at product cards and a shopping basket. This project goes further: after checkout, the order is handled by a multi-agent fulfilment workflow and enriched with AI-style prediction results.

The concept and system direction are designed around three university modules:

- Cloud Computing: data cleaning, frontend, backend APIs and deployment
- Multi-Agent Systems: autonomous order, inventory, coordinator and warehouse agents
- Neural Networks: demand prediction, fraud scoring and category classification

The goal is not just to build another shop UI, but to show how a small coursework foundation can grow into a realistic engineering portfolio project.

## What It Demonstrates

- A JavaScript product data cleaning pipeline for noisy e-commerce records
- A React shopping interface with search, sorting, in-stock filtering and basket checkout
- A FastAPI backend exposing product, order and agent endpoints
- A simplified Contract Net Protocol for warehouse bidding
- Demand prediction and fraud detection modules with stable inference interfaces
- Docker-ready backend structure for future cloud deployment
- A course intelligence dashboard showing how COMP315, COMP310 and ELEC320 map into the running system

## Why It Is Star-Worthy

This project is intentionally built as a learning bridge: simple enough for students to read, but structured enough to discuss with interviewers.

- It connects frontend, backend, agents and ML in one coherent flow.
- It shows how to upgrade coursework instead of abandoning it after submission.
- It keeps the first version runnable, then leaves clear upgrade paths for stronger models and deployment.
- It documents both the engineering structure and the thinking behind the project.

## Demo Flow

1. Raw product JSON is cleaned into stable product records.
2. The frontend loads products from the backend API.
3. A user searches, sorts, filters and adds products to the basket.
4. Checkout sends the basket to the backend order API.
5. Order Agent receives the order.
6. Fraud Detection Agent returns a risk score.
7. Inventory Agent checks stock availability.
8. Coordinator Agent asks Warehouse Agents for bids.
9. The best warehouse is selected.
10. Demand Prediction Agent estimates next 7-day demand.
11. The frontend displays order status, selected warehouse, risk score, predicted demand, warehouse bids, model evidence and the full decision log.

## Agent Layer

The order workflow is intentionally modelled as a multi-agent system rather than a single service function.

- Order Agent receives the checkout request and starts the fulfilment workflow.
- Fraud Detection Agent scores the order and decides whether review is required.
- Inventory Agent checks stock and reserves inventory after approval.
- Coordinator Agent announces the fulfilment task and selects the best warehouse bid.
- Warehouse Agents bid using workload, stock level, distance and processing speed, then return an explainable bid reason.
- Demand Prediction Agent estimates future demand and provides restock guidance.

## AI Layer

The first version uses lightweight deterministic model interfaces so the whole system can run immediately. These interfaces are designed to be replaced later by trained MLP, SVM or PyTorch models.

- Demand Prediction: product features to predicted next 7-day sales
- Fraud Detection: order features to a risk score from 0 to 1
- Category Classification: product text and metadata to category labels

## Project Structure

```text
data_cleaning/      Product data cleaning pipeline
frontend/           React e-commerce interface
backend/            FastAPI backend and multi-agent workflow
ml_models/          Demand, fraud and category prediction modules
docs/               Design notes and Chinese project explanation
tests/              Smoke tests for data cleaning and agent flow
```

## Quick Start

Clean sample product data:

```bash
node data_cleaning/data_processing.js \
  data_cleaning/raw_products/products.json \
  data_cleaning/cleaned_products/products.json
```

Run backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Run frontend:

```bash
cd frontend
npm install
npm run dev
```

Then open the frontend, add products to the basket and submit checkout.

## API Examples

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Create an order:

```bash
curl -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo-user","items":[{"product_id":"p-1001","quantity":1}],"shipping_distance":18,"is_new_user":true}'
```

Example response includes:

- `order_status`
- `selected_warehouse`
- `risk_score`
- `predicted_demand_next_7_days`
- `restock_recommendation`
- `bids`
- `decision_log`
- `course_trace`
- `model_evaluations`

## Roadmap

- Replace lightweight prediction modules with trained MLP/SVM models
- Add SQLite or PostgreSQL persistence for products, orders and agent logs
- Add dashboard charts for warehouse bids and demand forecasts
- Add screenshots and a short demo GIF for GitHub showcase
- Deploy backend and frontend with Docker Compose or a cloud VM

## Portfolio Summary

Extended a coursework-based React e-commerce prototype into an AI-powered multi-agent fulfilment system with backend APIs, autonomous agent coordination, explainable warehouse bidding, prediction modules, course mapping dashboards and Docker-ready deployment.

## 中文项目介绍

这是一个面向 GitHub 展示、面试讲解和本科生学习参考的 AI + Multi-Agent 电商系统项目。

项目的核心思路是：不从零开始造一个普通电商网站，而是把已有的课程作业基础继续工程化。原本的数据清洗和 React 电商前端，被扩展成一个包含后端 API、多智能体订单履约、需求预测、异常订单检测和 Docker 部署结构的完整项目。

这个项目适合向面试官说明三件事：

- 我能把课程作业升级成可运行、可展示、可继续迭代的工程项目。
- 我理解前端、后端、数据处理、Agent 协作、课程映射和 ML 推理接口之间的系统关系。
- 我能围绕一个业务流程讲清楚技术选择，而不是只堆技术名词。

这个项目也适合本科生参考：

- 可以学习如何把 coursework 变成 portfolio project。
- 可以参考 React + FastAPI + Agent workflow + course dashboard 的项目结构。
- 可以 fork 后继续加入数据库、真实 MLP 模型、仪表盘、部署和演示截图。

如果你正在准备 final-year project、GitHub portfolio 或软件工程 / AI 方向面试，这个仓库可以作为一个清晰的起点。欢迎 fork、学习、改造，也欢迎 star 支持。
