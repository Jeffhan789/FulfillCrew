# Cloud-Based Multi-Agent E-Commerce Intelligence System

An interview-ready AI + multi-agent e-commerce project built from a clear product idea: turn a simple coursework e-commerce prototype into a full order intelligence system.

中文名：云端多智能体智能电商系统

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
11. The frontend displays order status, selected warehouse, risk score, predicted demand and the full decision log.

## Agent Layer

The order workflow is intentionally modelled as a multi-agent system rather than a single service function.

- Order Agent receives the checkout request and starts the fulfilment workflow.
- Fraud Detection Agent scores the order and decides whether review is required.
- Inventory Agent checks stock and reserves inventory after approval.
- Coordinator Agent announces the fulfilment task and selects the best warehouse bid.
- Warehouse Agents bid using workload, stock level, distance and processing speed.
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
- `decision_log`

## Roadmap

- Replace lightweight prediction modules with trained MLP/SVM models
- Add SQLite or PostgreSQL persistence for products, orders and agent logs
- Add dashboard charts for warehouse bids and demand forecasts
- Add screenshots and a short demo GIF for GitHub showcase
- Deploy backend and frontend with Docker Compose or a cloud VM

## Portfolio Summary

Extended a coursework-based React e-commerce prototype into an AI-powered multi-agent fulfilment system with backend APIs, autonomous agent coordination, prediction modules and Docker-ready deployment.
