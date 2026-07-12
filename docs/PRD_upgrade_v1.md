# FulfillCrew Upgrade PRD — Event-Driven Multi-Agent E-Commerce Fulfillment System

> **Document Type:** Product Requirements Document
> **Version:** 1.0
> **Status:** Draft
> **Last Updated:** 2026-07-12
> **Scope:** Data layer, ML model, and real-time communication upgrades

---

## 1. Background & Problem Statement

### 1.1 Current State

FulfillCrew is a multi-agent order fulfillment system built on React + FastAPI + Python Agents. It demonstrates a complete checkout-to-fulfillment workflow: frontend basket → order API → fraud detection → inventory check → warehouse bidding → demand prediction. However, it remains at a **demo level** with the following limitations:

- All product/order data lives in memory; lost on restart
- Agent communication is synchronous function calls; blocking and non-scalable
- ML modules are deterministic stubs (heuristic rules) with no trained models
- No real-time feedback to the frontend; no observability
- Decision logs are ephemeral; no historical analysis possible

### 1.2 Industry Pain Points Addressed

Based on real 2025–2026 industry news (NVIDIA MAIW, 神州控股 AI Control Tower, Amazon AI Supply Chain, Shopify Fraud Control, Temu/Shein multi-warehouse fulfillment), the e-commerce fulfillment industry faces three core structural problems:

| # | Core Problem | Pain Points | Why It Matters |
|---|-------------|-------------|--------------|
| A | **Data silos + disconnected decisions** | Warehouses have no "brain"; AI predictions never trigger actions; multi-warehouse collaboration is manual | Systems are fragmented; decisions rely on human experience and quarterly reviews |
| B | **Predictions are inaccurate and unexplainable** | Demand forecasting errors cause stockouts or overstock; fraud detection relies on static rules and manual review | Without trained models, predictions are unreliable; without explainability, decisions are untrusted |
| C | **Systems lack real-time feedback and elasticity** | Peak season volume surges 3–5x and systems crash; no real-time monitoring or alerts | Reactive systems cannot handle spikes; outages are discovered by customers, not dashboards |

### 1.3 Project Goal

Upgrade FulfillCrew from a **demo-level coursework project** to an **interview-ready, industry-informed engineering portfolio** that demonstrates:

1. **Architecture capability** — event-driven, decoupled, observable system design
2. **ML engineering capability** — trained models with evaluation metrics and explainability
3. **Real-time systems capability** — WebSocket, async processing, health monitoring

The upgrade should be **completable within a focused development period**, not a commercial product roadmap.

---

## 2. Scope & Out-of-Scope

### 2.1 In-Scope

| Phase | Component | Description |
|-------|-----------|-------------|
| Phase 1 | PostgreSQL persistence | Product, order, inventory, agent decision logs stored in relational database |
| Phase 1 | Redis event bus | Lightweight pub/sub for async inter-agent communication |
| Phase 2 | MLP demand prediction | Trained PyTorch MLP model with real dataset, MAE/MAPE evaluation |
| Phase 2 | XGBoost fraud detection | Trained XGBoost classifier with SHAP explainability, ROC-AUC evaluation |
| Phase 3 | WebSocket real-time | Order status pushed to frontend in real time |
| Phase 3 | Observability | Structured logging (structlog), Prometheus metrics, health check API |
| Phase 3 | Frontend dashboard | Recharts visualizations for orders, bids, predictions, risk scores |

### 2.2 Out-of-Scope (Explicitly Excluded to Avoid Redundancy)

| Item | Why Excluded |
|------|-------------|
| Reinforcement learning warehouse selection | Too complex for a portfolio project; Thompson Sampling is hard to explain in interviews; fixed-rule bidding is sufficient for demonstration |
| Kubernetes / production-grade deployment | Docker Compose is sufficient for a portfolio; K8s adds complexity without interview value |
| A/B testing framework | No real traffic to test against; would be a hollow feature |
| Full Event Sourcing / CQRS | Redis Pub/Sub is sufficient for async communication; full CQRS is overkill |
| Multi-region / distributed deployment | Single-node deployment is sufficient for interview demonstration |
| Real-time feature store | External signal ingestion (weather, social media) is valuable but requires paid APIs and infrastructure beyond scope |
| Order payment integration | Payment is a separate domain; this project focuses on fulfillment post-checkout |

---

## 3. Detailed Requirements

### 3.1 Phase 1: Data Layer — PostgreSQL + Redis Event Bus

#### 3.1.1 Database Schema

**Tables:**

```sql
-- Products (cleaned data, populated from data_cleaning pipeline)
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    type TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    rating REAL NOT NULL,
    image_link TEXT
);

-- Orders (persisted checkout requests)
CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'guest',
    order_status TEXT NOT NULL, -- created, review_required, rejected_out_of_stock
    order_total REAL NOT NULL,
    selected_warehouse TEXT,
    risk_score REAL,
    fraud_status TEXT,
    predicted_demand INTEGER,
    restock_recommendation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Order Items (line items per order)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id UUID REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id TEXT REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL
);

-- Agent Decisions (audit trail of every agent step)
CREATE TABLE agent_decisions (
    id SERIAL PRIMARY KEY,
    order_id UUID REFERENCES orders(order_id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    decision_type TEXT NOT NULL, -- fraud_check, inventory_check, warehouse_bid, etc.
    decision_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Warehouse Bids (record of all bids per order)
CREATE TABLE warehouse_bids (
    id SERIAL PRIMARY KEY,
    order_id UUID REFERENCES orders(order_id) ON DELETE CASCADE,
    warehouse_id TEXT NOT NULL,
    bid_value REAL NOT NULL,
    workload INTEGER,
    distance REAL,
    stock_level INTEGER,
    processing_speed REAL,
    suitability_score REAL,
    reason TEXT,
    is_winner BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3.1.2 Data Access Layer (Repository Pattern)

```python
# backend/repositories/product_repository.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Product

class ProductRepository:
    """Async repository for product CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, product_id: str) -> Optional[Product]:
        ...

    async def update_stock(self, product_id: str, delta: int) -> None:
        ...
```

#### 3.1.3 Redis Event Bus

```python
# backend/infrastructure/event_bus.py
import redis.asyncio as redis
from typing import Callable, Any
import json

class RedisEventBus:
    """Lightweight async event bus for inter-agent communication."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.client = redis.from_url(redis_url)
        self.subscribers: dict[str, list[Callable]] = {}

    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        """Publish an event to a channel."""
        await self.client.publish(channel, json.dumps(event))

    async def subscribe(self, channel: str, handler: Callable) -> None:
        """Subscribe a handler to a channel."""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(handler)

    # Event channels:
    # - order.created
    # - fraud.checked
    # - inventory.checked
    # - warehouse.bid
    # - fulfillment.completed
```

**Event Flow:**

```
order.created
    ├── fraud.checked → publish(fraud.checked, {order_id, risk_score, fraud_status})
    ├── inventory.checked → publish(inventory.checked, {order_id, stock_available, unavailable})
    ├── warehouse.bid → publish(warehouse.bid, {order_id, bids, winner})
    └── fulfillment.completed → publish(fulfillment.completed, {order_id, status, predictions})
```

#### 3.1.4 Acceptance Criteria

| # | Criteria | How to Verify |
|---|----------|-------------|
| 1.1 | Products loaded from PostgreSQL, not in-memory dict | Restart backend; products still available via API |
| 1.2 | Orders are persisted with full line items | Create order; query DB; order + items exist in tables |
| 1.3 | Agent decisions are logged in `agent_decisions` table | Create order; query `agent_decisions`; ≥4 rows (fraud, inventory, coordinator, demand) |
| 1.4 | Warehouse bids are recorded in `warehouse_bids` table | Create order; query `warehouse_bids`; 3 rows (one per warehouse) with winner marked |
| 1.5 | Event bus delivers messages between agents | Subscribe to `order.created`; publish event; handler receives it within 100ms |
| 1.6 | All database operations are async | No synchronous SQLAlchemy calls in request path |

---

### 3.2 Phase 2: ML Model Upgrade — Trained MLP + XGBoost with SHAP

#### 3.2.1 Demand Prediction Model (MLP Regression)

**Model Requirements:**

| Attribute | Specification |
|-----------|-------------|
| Framework | PyTorch |
| Architecture | 2-layer MLP (input → 64 → 32 → 1) with ReLU, Dropout(0.2) |
| Input features | price, rating, category_encoded, type_encoded, day_of_week, month, is_weekend, sales_last_7_days, sales_last_30_days |
| Output | Predicted sales for next 7 days (integer) |
| Loss function | MSE (Mean Squared Error) |
| Optimizer | Adam, lr=0.001 |
| Training data | UCI Online Retail Dataset or Kaggle E-commerce Data |
| Evaluation metrics | MAE, MAPE, R² |
| Target MAE | < 50 units (dataset-dependent) |

**Inference API:**

```python
# ml_models/demand_prediction/predict.py
class DemandPredictor:
    """Trained MLP demand prediction model with evaluation metrics."""

    def __init__(self, model_path: str):
        self.model = torch.load(model_path, map_location='cpu')
        self.model.eval()

    def predict(self, product_features: dict) -> int:
        """Return predicted next 7-day sales as integer."""
        ...

    def evaluate(self, test_data: pd.DataFrame) -> dict[str, float]:
        """Return MAE, MAPE, R² on test set."""
        ...
```

#### 3.2.2 Fraud Detection Model (XGBoost + SHAP)

**Model Requirements:**

| Attribute | Specification |
|-----------|-------------|
| Framework | XGBoost |
| Type | Binary classifier |
| Input features | order_total, number_of_items, average_item_price, is_new_user, account_age_days, shipping_distance, billing_shipping_match, order_hour, is_night_order, orders_in_last_hour |
| Output | Risk score (0.0–1.0) + binary decision (approved / review_required) |
| Class imbalance | Use `scale_pos_weight` (fraud ~1% of orders) |
| Evaluation metrics | ROC-AUC, PR-AUC, Precision@threshold, Recall@threshold |
| Target ROC-AUC | ≥ 0.90 |
| Explainability | SHAP TreeExplainer; per-feature contribution returned in API response |

**Inference API:**

```python
# ml_models/fraud_detection/predict.py
class FraudDetector:
    """Trained XGBoost fraud detector with SHAP explainability."""

    def __init__(self, model_path: str):
        self.model = xgb.Booster().load_model(model_path)
        self.explainer = shap.TreeExplainer(self.model)

    def score(self, order_features: dict) -> tuple[float, str, dict]:
        """
        Returns:
            risk_score (float): 0.0–1.0
            decision (str): "approved" or "review_required"
            shap_explanation (dict): per-feature contribution
        """
        ...
```

#### 3.2.3 Product Category Classifier (Lightweight Upgrade)

**Current:** Keyword-based heuristic rules
**Upgrade:** TF-IDF + Logistic Regression trained on product descriptions
**Reason:** Demonstrates NLP pipeline + text classification; lightweight enough to train quickly

```python
# ml_models/product_category_classifier/train.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Train on product name + description → predict category
vectorizer = TfidfVectorizer(max_features=1000)
classifier = LogisticRegression(multi_class='multinomial', max_iter=1000)
```

#### 3.2.4 Acceptance Criteria

| # | Criteria | How to Verify |
|---|----------|-------------|
| 2.1 | Demand prediction model trained on real dataset | `python ml_models/demand_prediction/train.py` completes without error; model file saved |
| 2.2 | Demand prediction MAE < 50 on test set | `python ml_models/demand_prediction/evaluate.py` outputs MAE |
| 2.3 | Fraud detection model trained with ROC-AUC ≥ 0.90 | `python ml_models/fraud_detection/evaluate.py` outputs ROC-AUC |
| 2.4 | Fraud API returns SHAP explanation | Create order; response includes `shap_explanation` field with per-feature contributions |
| 2.5 | Category classifier trained on product text | `python ml_models/product_category_classifier/train.py` completes; accuracy > 70% |
| 2.6 | All three models have `train.py`, `evaluate.py`, `predict.py` scripts | File structure matches spec |

---

### 3.3 Phase 3: Real-Time + Observability

#### 3.3.1 WebSocket Order Status Push

```python
# backend/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    """Manage WebSocket connections for real-time order updates."""

    async def connect(self, websocket: WebSocket, order_id: str):
        await websocket.accept()
        self.active_connections[order_id] = websocket

    async def send_order_update(self, order_id: str, data: dict):
        if order_id in self.active_connections:
            await self.active_connections[order_id].send_json(data)
```

**Frontend Integration:**

```typescript
// frontend/src/hooks/useOrderSocket.ts
const useOrderSocket = (orderId: string) => {
    const [status, setStatus] = useState(null);
    useEffect(() => {
        const ws = new WebSocket(`ws://localhost:8000/ws/orders/${orderId}`);
        ws.onmessage = (event) => setStatus(JSON.parse(event.data));
        return () => ws.close();
    }, [orderId]);
    return status;
};
```

#### 3.3.2 Structured Logging

**Every agent decision must emit a structured log:**

```json
{
    "event": "agent_decision",
    "timestamp": "2026-07-12T14:30:00Z",
    "order_id": "uuid",
    "agent": "FraudDetectionAgent",
    "decision_type": "fraud_check",
    "risk_score": 0.85,
    "threshold": 0.7,
    "decision": "review_required",
    "shap_explanation": {
        "shipping_distance": 0.32,
        "is_new_user": 0.28,
        "order_total": 0.15
    },
    "latency_ms": 12
}
```

**Tech:** `structlog` + JSON formatter

#### 3.3.3 Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

orders_total = Counter('fulfillcrew_orders_total', 'Total orders', ['status'])
order_processing_duration = Histogram('fulfillcrew_order_processing_seconds', 'Order processing time')
warehouse_bids_total = Counter('fulfillcrew_warehouse_bids_total', 'Total bids', ['warehouse_id'])
prediction_mae = Gauge('fulfillcrew_demand_prediction_mae', 'Current MAE')
fraud_roc_auc = Gauge('fulfillcrew_fraud_detection_auc', 'Current ROC-AUC')
```

**Metrics endpoint:** `GET /metrics` (Prometheus scrape format)

#### 3.3.4 Health Check API

```python
@router.get("/health")
async def health_check():
    checks = {
        "database": await check_db_connection(),
        "redis": await check_redis_connection(),
        "demand_model": demand_predictor.is_loaded(),
        "fraud_model": fraud_detector.is_loaded(),
    }
    return {
        "status": "healthy" if all(checks.values()) else "degraded",
        "checks": checks,
    }
```

#### 3.3.5 Frontend Dashboard (Recharts)

**Charts:**

| Chart | Data Source | Purpose |
|-------|-------------|---------|
| Order status timeline | WebSocket real-time | Show order progressing through agents |
| Warehouse bid comparison | Order API response | Bar chart of 3 warehouse bids |
| Demand prediction trend | Order API + historical | 7-day forecast line chart |
| Risk score gauge | Order API response | Circular gauge for risk_score (0-1) |
| System health panel | `/health` + `/metrics` | Green/yellow/red status indicators |
| Agent decision log | Order API response | Timeline of all agent decisions with timestamps |

**Tech:** Recharts + TanStack Query + Zustand

#### 3.3.6 Acceptance Criteria

| # | Criteria | How to Verify |
|---|----------|-------------|
| 3.1 | WebSocket pushes order status updates within 100ms of agent decision | Open browser dev tools; checkout; observe WebSocket messages |
| 3.2 | Structured logs contain all agent decisions in JSON format | Checkout; inspect backend logs; verify JSON structure |
| 3.3 | `/metrics` endpoint returns Prometheus-compatible metrics | `curl /metrics`; verify counters and gauges present |
| 3.4 | `/health` endpoint checks DB, Redis, and model load status | `curl /health`; verify all checks pass |
| 3.5 | Frontend dashboard shows ≥4 charts (bids, prediction, risk, status) | Open frontend; verify charts render with data |
| 3.6 | Agent decision log is visible in frontend with timestamps | Open frontend; click order details; verify decision timeline |

---

## 4. Technical Architecture

### 4.1 System Diagram (Post-Upgrade)

```
┌─────────────────────────────────────────────────────────────────────┐
│                           React Frontend                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Product  │  │  Basket  │  │  Order   │  │ Dashboard (Recharts) │  │
│  │  List    │  │          │  │  Status  │  │  - Bids chart        │  │
│  │          │  │          │  │  (WebSocket) │  - Prediction trend │  │
│  │          │  │          │  │          │  │  - Risk gauge        │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │ HTTP/WebSocket
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Products │  │  Orders  │  │  Agents  │  │  /health /metrics    │  │
│  │  Router  │  │  Router  │  │  Router  │  │  /ws/orders/:id      │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘  │
│       │             │             │                                   │
│       ▼             ▼             ▼                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Product  │  │  Order   │  │  Agent   │  │  WebSocket Manager   │  │
│  │ Service  │  │  Service │  │  Service │  │  (ConnectionManager) │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘  │
│       │             │             │                                   │
│       ▼             ▼             ▼                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Product  │  │  Order   │  │  Redis   │  │  ML Models           │  │
│  │  Repo    │  │  Repo    │  │  Event   │  │  - MLP Demand        │  │
│  │ (async)  │  │ (async)  │  │   Bus    │  │  - XGBoost Fraud     │  │
│  └──────────┘  └──────────┘  └──────────┘  │  - TF-IDF Category   │  │
│       │             │             │         └──────────────────────┘  │
│       ▼             ▼             ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              PostgreSQL 14 + Redis 7                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │ products │  │  orders  │  │order_items│  │warehouse_│    │   │
│  │  │          │  │          │  │           │  │   bids   │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │              agent_decisions                        │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Frontend | React | 18.3 | UI framework |
| Frontend | TypeScript | 5.7 | Type safety |
| Frontend | Vite | 6.0 | Build tool |
| Frontend | Recharts | 2.x | Data visualization |
| Frontend | TanStack Query | 5.x | Data fetching + caching |
| Frontend | Zustand | 4.x | State management |
| Backend | Python | 3.12 | Runtime |
| Backend | FastAPI | 0.115 | API framework |
| Backend | SQLAlchemy | 2.0 | ORM |
| Backend | asyncpg | 0.29 | Async PostgreSQL driver |
| Backend | Redis | 7.x | Cache + message broker |
| Backend | redis-py | 5.x | Redis client |
| Backend | structlog | 24.x | Structured logging |
| Backend | prometheus-client | 0.21 | Metrics |
| Backend | PyTorch | 2.3 | MLP training |
| Backend | XGBoost | 2.0 | Fraud classifier |
| Backend | SHAP | 0.45 | Model explainability |
| Backend | scikit-learn | 1.4 | TF-IDF + Logistic Regression |
| Backend | pytest | 8.3 | Testing |
| Backend | httpx | 0.28 | HTTP client (TestClient) |
| Database | PostgreSQL | 14+ | Relational data store |
| Infra | Docker | 24+ | Containerization |
| Infra | Docker Compose | 2.20+ | Multi-service orchestration |

### 4.3 Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/fulfillcrew

# Redis
REDIS_URL=redis://localhost:6379/0

# ML Models
DEMAND_MODEL_PATH=ml_models/demand_prediction/models/demand_predictor.pt
FRAUD_MODEL_PATH=ml_models/fraud_detection/models/fraud_detector.json
CATEGORY_MODEL_PATH=ml_models/product_category_classifier/models/classifier.pkl

# Backend
BACKEND_PORT=8000
BACKEND_LOG_LEVEL=info
CORS_ORIGINS=http://localhost:5173,http://localhost:8080

# Frontend
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_WS_BASE_URL=ws://127.0.0.1:8000
```

---

## 5. Non-Functional Requirements

| # | Requirement | Target | Rationale |
|---|-------------|--------|-----------|
| N1 | API response time (p95) | < 200ms | Acceptable for demo; real systems target <100ms |
| N2 | WebSocket latency | < 100ms | Real-time feel for frontend |
| N3 | Database query time (p95) | < 50ms | Async queries should be fast |
| N4 | Test coverage | ≥ 80% | Portfolio project standard |
| N5 | Docker build time | < 120s | Reasonable for CI/CD |
| N6 | Docker image size | < 500MB | Python + ML models are heavy; multi-stage build required |
| N7 | Frontend bundle size | < 500KB | Vite tree-shaking should keep it small |
| N8 | Concurrent WebSocket connections | ≥ 100 | Sufficient for demo and load testing |
| N9 | Model inference time | < 50ms | MLP and XGBoost are lightweight; should be fast on CPU |
| N10 | Log retention | 30 days | Sufficient for development and demo |

---

## 6. API Specification Changes

### 6.1 New Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| WS | `/ws/orders/{order_id}` | WebSocket connection for real-time order updates | None |
| GET | `/health` | Comprehensive health check (DB, Redis, models) | None |
| GET | `/metrics` | Prometheus metrics endpoint | None |

### 6.2 Modified Endpoints

**POST /orders** (response enriched):

```json
{
    "order_id": "uuid",
    "order_status": "created",
    "order_total": 123.45,
    "selected_warehouse": "Warehouse A",
    "risk_score": 0.23,
    "fraud_status": "approved",
    "predicted_demand_next_7_days": 45,
    "restock_recommendation": "no restock needed",
    "bids": [...],
    "decision_log": [
        {
            "agent": "FraudDetectionAgent",
            "message": "Risk score 0.23; status approved.",
            "timestamp": "2026-07-12T14:30:00Z"
        }
    ],
    "course_trace": [...],
    "model_evaluations": [
        {
            "model_name": "Demand Prediction MLP",
            "score": 45,
            "mae": 32.5,
            "shap_explanation": null
        },
        {
            "model_name": "Fraud Detection XGBoost",
            "score": 0.23,
            "roc_auc": 0.94,
            "shap_explanation": {
                "shipping_distance": 0.05,
                "is_new_user": 0.08,
                "order_total": 0.02
            }
        }
    ]
}
```

**GET /agents/model-evaluations** (enriched with live metrics):

```json
{
    "models": [
        {
            "model_name": "Demand Prediction MLP",
            "status": "loaded",
            "mae": 32.5,
            "mape": 0.15,
            "r2": 0.82
        },
        {
            "model_name": "Fraud Detection XGBoost",
            "status": "loaded",
            "roc_auc": 0.94,
            "pr_auc": 0.71
        }
    ]
}
```

---

## 7. Risk Assessment & Mitigation

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | PostgreSQL async driver complexity | Medium | Medium | Use SQLAlchemy 2.0 async patterns; keep queries simple |
| R2 | XGBoost model overfitting on small dataset | Medium | High | Use cross-validation; regularization; early stopping |
| R3 | SHAP dependency conflicts with PyTorch | Low | Medium | Use separate virtual environments or Docker containers for training vs inference |
| R4 | WebSocket connection leaks | Medium | Medium | Implement connection manager with cleanup on disconnect |
| R5 | Redis not available in development environment | Medium | Low | Provide local Docker Compose with Redis; fallback to in-memory event bus for testing |
| R6 | Frontend bundle size exceeds target due to Recharts | Low | Medium | Use tree-shaking; only import needed chart components |
| R7 | Docker build exceeds time limit | Medium | Low | Multi-stage build; cache pip/npm layers; use slim base images |
| R8 | MAE/ROC-AUC targets not met on first training | High | Medium | Iterate on feature engineering; try alternative architectures; document results honestly |

---

## 8. Success Criteria

This upgrade is considered successful if all of the following are met:

1. **Backend starts** with PostgreSQL + Redis and passes `/health` check
2. **54 original tests** still pass (backward compatibility)
3. **New tests** cover Phase 1–3 with ≥ 80% coverage
4. **ML models** are trained on real data with evaluation metrics documented
5. **WebSocket** pushes order updates to frontend in real time
6. **Frontend dashboard** shows at least 4 charts with live data
7. **Docker Compose** starts full stack (frontend + backend + PostgreSQL + Redis) with one command
8. **README** is updated with bilingual documentation of new architecture

---

---

# FulfillCrew 升级 PRD — 智仓通（事件驱动多智能体电商订单履约系统）

> **文档类型：** 产品需求文档
> **版本：** 1.0
> **状态：** 草稿
> **最后更新：** 2026-07-12
> **范围：** 数据层、机器学习模型、实时通信升级

---

## 1. 背景与问题陈述

### 1.1 当前状态

FulfillCrew（智仓通）是一个基于 React + FastAPI + Python Agent 的多智能体订单履约系统，展示了完整的"下单→履约"工作流：前端购物篮 → 订单 API → 欺诈检测 → 库存检查 → 仓库竞价 → 需求预测。但它仍停留在**演示级别**，存在以下限制：

- 所有商品/订单数据存在内存中，重启丢失
- Agent 间通信是同步函数调用，阻塞且不可扩展
- ML 模块是确定性桩代码（启发式规则），没有训练好的模型
- 没有实时反馈给前端，没有可观测性
- 决策日志是临时的，无法进行历史分析

### 1.2 行业痛点对应

基于 2025-2026 年真实行业新闻（NVIDIA MAIW、神州控股 AI 控制塔、Amazon AI 供应链、Shopify Fraud Control、Temu/Shein 多仓履约），电商履约行业面临三个核心结构性问题：

| # | 核心问题 | 包含痛点 | 为什么重要 |
|---|---------|---------|-----------|
| A | **数据不通 + 决策不联动** | 仓库没有"大脑"；AI 预测无法触发行动；多仓协同靠人工 | 系统碎片化；决策依赖人工经验和季度复盘 |
| B | **预测不准且不可解释** | 需求预测不准导致积压/断货；欺诈检测靠静态规则和人工审核 | 没有训练好的模型，预测不可靠；没有可解释性，决策不受信任 |
| C | **系统缺乏实时反馈和弹性** | 旺季峰值 3-5x 系统崩溃；没有实时监控和告警 | 被动系统无法应对峰值；宕机由客户发现，而非仪表盘 |

### 1.3 项目目标

将 FulfillCrew 从**演示级课程作业**升级为**面试就绪、行业认可的工程作品集**，展示：

1. **架构能力** — 事件驱动、解耦、可观测的系统设计
2. **机器学习工程能力** — 训练好的模型 + 评估指标 + 可解释性
3. **实时系统能力** — WebSocket、异步处理、健康监控

升级应在一个**聚焦的开发周期内可完成**，不是商业产品路线图。

---

## 2. 范围与排除项

### 2.1 范围内

| 阶段 | 组件 | 说明 |
|------|------|------|
| 阶段 1 | PostgreSQL 持久化 | 商品、订单、库存、Agent 决策日志存储在关系数据库 |
| 阶段 1 | Redis 事件总线 | 轻量级 pub/sub，用于 Agent 间异步通信 |
| 阶段 2 | MLP 需求预测 | 用真实数据集训练的 PyTorch MLP 模型，MAE/MAPE 评估 |
| 阶段 2 | XGBoost 欺诈检测 | 训练好的 XGBoost 分类器 + SHAP 可解释性，ROC-AUC 评估 |
| 阶段 3 | WebSocket 实时推送 | 订单状态实时推送到前端 |
| 阶段 3 | 可观测性 | 结构化日志（structlog）、Prometheus 指标、健康检查 API |
| 阶段 3 | 前端仪表盘 | Recharts 可视化：订单、竞价、预测、风险评分 |

### 2.2 范围外（明确排除以避免冗余）

| 项目 | 排除原因 |
|------|---------|
| 强化学习仓库选择 | 对作品集项目过于复杂；Thompson Sampling 面试难讲清楚；固定规则竞价已足够演示 |
| Kubernetes / 生产级部署 | Docker Compose 对作品集足够；K8s 增加复杂度但没有面试价值 |
| A/B 测试框架 | 没有真实流量来测试；会是空壳功能 |
| 完整事件溯源 / CQRS | Redis Pub/Sub 已足够支持异步通信；完整 CQRS 过度设计 |
| 多区域 / 分布式部署 | 单节点部署对面试演示足够 |
| 实时特征商店 | 外部信号采集（天气、社交媒体）需要付费 API 和基础设施，超出范围 |
| 订单支付集成 | 支付是独立领域；本项目聚焦结账后的履约 |

---

## 3. 详细需求

### 3.1 阶段 1：数据层 — PostgreSQL + Redis 事件总线

#### 3.1.1 数据库 Schema

**表结构：**

```sql
-- 商品（清洗后的数据，由 data_cleaning pipeline 填充）
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    type TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    rating REAL NOT NULL,
    image_link TEXT
);

-- 订单（持久化的结账请求）
CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'guest',
    order_status TEXT NOT NULL, -- created, review_required, rejected_out_of_stock
    order_total REAL NOT NULL,
    selected_warehouse TEXT,
    risk_score REAL,
    fraud_status TEXT,
    predicted_demand INTEGER,
    restock_recommendation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 订单明细（每个订单的行项目）
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id UUID REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id TEXT REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL
);

-- Agent 决策（每一步 Agent 的审计追踪）
CREATE TABLE agent_decisions (
    id SERIAL PRIMARY KEY,
    order_id UUID REFERENCES orders(order_id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    decision_type TEXT NOT NULL, -- fraud_check, inventory_check, warehouse_bid 等
    decision_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 仓库竞价（每个订单的所有竞价记录）
CREATE TABLE warehouse_bids (
    id SERIAL PRIMARY KEY,
    order_id UUID REFERENCES orders(order_id) ON DELETE CASCADE,
    warehouse_id TEXT NOT NULL,
    bid_value REAL NOT NULL,
    workload INTEGER,
    distance REAL,
    stock_level INTEGER,
    processing_speed REAL,
    suitability_score REAL,
    reason TEXT,
    is_winner BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3.1.2 数据访问层（Repository 模式）

```python
# backend/repositories/product_repository.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Product

class ProductRepository:
    """商品的异步 Repository CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, product_id: str) -> Optional[Product]:
        ...

    async def update_stock(self, product_id: str, delta: int) -> None:
        ...
```

#### 3.1.3 Redis 事件总线

```python
# backend/infrastructure/event_bus.py
import redis.asyncio as redis
from typing import Callable, Any
import json

class RedisEventBus:
    """轻量级异步事件总线，用于 Agent 间通信。"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.client = redis.from_url(redis_url)
        self.subscribers: dict[str, list[Callable]] = {}

    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        """发布事件到频道。"""
        await self.client.publish(channel, json.dumps(event))

    async def subscribe(self, channel: str, handler: Callable) -> None:
        """订阅处理程序到频道。"""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(handler)

    # 事件频道：
    # - order.created
    # - fraud.checked
    # - inventory.checked
    # - warehouse.bid
    # - fulfillment.completed
```

**事件流：**

```
order.created
    ├── fraud.checked → publish(fraud.checked, {order_id, risk_score, fraud_status})
    ├── inventory.checked → publish(inventory.checked, {order_id, stock_available, unavailable})
    ├── warehouse.bid → publish(warehouse.bid, {order_id, bids, winner})
    └── fulfillment.completed → publish(fulfillment.completed, {order_id, status, predictions})
```

#### 3.1.4 验收标准

| # | 标准 | 验证方式 |
|---|------|---------|
| 1.1 | 商品从 PostgreSQL 加载，非内存字典 | 重启后端；商品仍可通过 API 获取 |
| 1.2 | 订单持久化，包含完整行项目 | 创建订单；查询数据库；订单 + 行项目存在于表中 |
| 1.3 | Agent 决策记录在 `agent_decisions` 表中 | 创建订单；查询 `agent_decisions`；≥4 行（欺诈、库存、协调、需求） |
| 1.4 | 仓库竞价记录在 `warehouse_bids` 表中 | 创建订单；查询 `warehouse_bids`；3 行（每个仓库一行），winner 已标记 |
| 1.5 | 事件总线在 Agent 间传递消息 | 订阅 `order.created`；发布事件；处理程序在 100ms 内收到 |
| 1.6 | 所有数据库操作都是异步的 | 请求路径中无同步 SQLAlchemy 调用 |

---

### 3.2 阶段 2：ML 模型升级 — 训练好的 MLP + XGBoost + SHAP

#### 3.2.1 需求预测模型（MLP 回归）

**模型需求：**

| 属性 | 规格 |
|------|------|
| 框架 | PyTorch |
| 架构 | 2 层 MLP（输入 → 64 → 32 → 1），ReLU，Dropout(0.2) |
| 输入特征 | price, rating, category_encoded, type_encoded, day_of_week, month, is_weekend, sales_last_7_days, sales_last_30_days |
| 输出 | 未来 7 天预测销量（整数） |
| 损失函数 | MSE（均方误差） |
| 优化器 | Adam, lr=0.001 |
| 训练数据 | UCI Online Retail Dataset 或 Kaggle E-commerce Data |
| 评估指标 | MAE, MAPE, R² |
| 目标 MAE | < 50（取决于数据集） |

**推理 API：**

```python
# ml_models/demand_prediction/predict.py
class DemandPredictor:
    """训练好的 MLP 需求预测模型，带评估指标。"""

    def __init__(self, model_path: str):
        self.model = torch.load(model_path, map_location='cpu')
        self.model.eval()

    def predict(self, product_features: dict) -> int:
        """返回未来 7 天预测销量（整数）。"""
        ...

    def evaluate(self, test_data: pd.DataFrame) -> dict[str, float]:
        """返回测试集上的 MAE, MAPE, R²。"""
        ...
```

#### 3.2.2 欺诈检测模型（XGBoost + SHAP）

**模型需求：**

| 属性 | 规格 |
|------|------|
| 框架 | XGBoost |
| 类型 | 二分类器 |
| 输入特征 | order_total, number_of_items, average_item_price, is_new_user, account_age_days, shipping_distance, billing_shipping_match, order_hour, is_night_order, orders_in_last_hour |
| 输出 | 风险评分（0.0–1.0）+ 二分类决策（approved / review_required） |
| 类别不平衡 | 使用 `scale_pos_weight`（欺诈约占订单 1%） |
| 评估指标 | ROC-AUC, PR-AUC, Precision@threshold, Recall@threshold |
| 目标 ROC-AUC | ≥ 0.90 |
| 可解释性 | SHAP TreeExplainer；API 响应返回每个特征的贡献度 |

**推理 API：**

```python
# ml_models/fraud_detection/predict.py
class FraudDetector:
    """训练好的 XGBoost 欺诈检测器，带 SHAP 可解释性。"""

    def __init__(self, model_path: str):
        self.model = xgb.Booster().load_model(model_path)
        self.explainer = shap.TreeExplainer(self.model)

    def score(self, order_features: dict) -> tuple[float, str, dict]:
        """
        返回：
            risk_score (float): 0.0–1.0
            decision (str): "approved" 或 "review_required"
            shap_explanation (dict): 每个特征的贡献度
        """
        ...
```

#### 3.2.3 商品分类器（轻量升级）

**当前：** 基于关键词的启发式规则
**升级：** 在商品描述上训练 TF-IDF + Logistic Regression
**原因：** 展示 NLP pipeline + 文本分类；轻量到可以快速训练

```python
# ml_models/product_category_classifier/train.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# 在商品名称 + 描述上训练 → 预测分类
vectorizer = TfidfVectorizer(max_features=1000)
classifier = LogisticRegression(multi_class='multinomial', max_iter=1000)
```

#### 3.2.4 验收标准

| # | 标准 | 验证方式 |
|---|------|---------|
| 2.1 | 需求预测模型在真实数据集上训练完成 | `python ml_models/demand_prediction/train.py` 无错误完成；模型文件已保存 |
| 2.2 | 需求预测 MAE < 50 | `python ml_models/demand_prediction/evaluate.py` 输出 MAE |
| 2.3 | 欺诈检测模型 ROC-AUC ≥ 0.90 | `python ml_models/fraud_detection/evaluate.py` 输出 ROC-AUC |
| 2.4 | 欺诈 API 返回 SHAP 解释 | 创建订单；响应包含 `shap_explanation` 字段，每个特征有贡献度 |
| 2.5 | 分类器在商品文本上训练完成 | `python ml_models/product_category_classifier/train.py` 完成；准确率 > 70% |
| 2.6 | 三个模型都有 `train.py`、`evaluate.py`、`predict.py` 脚本 | 文件结构符合规范 |

---

### 3.3 阶段 3：实时性 + 可观测性

#### 3.3.1 WebSocket 订单状态推送

```python
# backend/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    """管理 WebSocket 连接，实现实时订单更新。"""

    async def connect(self, websocket: WebSocket, order_id: str):
        await websocket.accept()
        self.active_connections[order_id] = websocket

    async def send_order_update(self, order_id: str, data: dict):
        if order_id in self.active_connections:
            await self.active_connections[order_id].send_json(data)
```

**前端集成：**

```typescript
// frontend/src/hooks/useOrderSocket.ts
const useOrderSocket = (orderId: string) => {
    const [status, setStatus] = useState(null);
    useEffect(() => {
        const ws = new WebSocket(`ws://localhost:8000/ws/orders/${orderId}`);
        ws.onmessage = (event) => setStatus(JSON.parse(event.data));
        return () => ws.close();
    }, [orderId]);
    return status;
};
```

#### 3.3.2 结构化日志

**每个 Agent 决策必须发出结构化日志：**

```json
{
    "event": "agent_decision",
    "timestamp": "2026-07-12T14:30:00Z",
    "order_id": "uuid",
    "agent": "FraudDetectionAgent",
    "decision_type": "fraud_check",
    "risk_score": 0.85,
    "threshold": 0.7,
    "decision": "review_required",
    "shap_explanation": {
        "shipping_distance": 0.32,
        "is_new_user": 0.28,
        "order_total": 0.15
    },
    "latency_ms": 12
}
```

**技术：** `structlog` + JSON 格式化器

#### 3.3.3 Prometheus 指标

```python
from prometheus_client import Counter, Histogram, Gauge

orders_total = Counter('fulfillcrew_orders_total', 'Total orders', ['status'])
order_processing_duration = Histogram('fulfillcrew_order_processing_seconds', 'Order processing time')
warehouse_bids_total = Counter('fulfillcrew_warehouse_bids_total', 'Total bids', ['warehouse_id'])
prediction_mae = Gauge('fulfillcrew_demand_prediction_mae', 'Current MAE')
fraud_roc_auc = Gauge('fulfillcrew_fraud_detection_auc', 'Current ROC-AUC')
```

**指标端点：** `GET /metrics`（Prometheus 抓取格式）

#### 3.3.4 健康检查 API

```python
@router.get("/health")
async def health_check():
    checks = {
        "database": await check_db_connection(),
        "redis": await check_redis_connection(),
        "demand_model": demand_predictor.is_loaded(),
        "fraud_model": fraud_detector.is_loaded(),
    }
    return {
        "status": "healthy" if all(checks.values()) else "degraded",
        "checks": checks,
    }
```

#### 3.3.5 前端仪表盘（Recharts）

**图表：**

| 图表 | 数据源 | 用途 |
|------|--------|------|
| 订单状态时间线 | WebSocket 实时 | 展示订单在 Agent 间的处理进度 |
| 仓库竞价对比 | 订单 API 响应 | 三个仓库竞价的柱状图 |
| 需求预测趋势 | 订单 API + 历史 | 7 天预测折线图 |
| 风险评分仪表盘 | 订单 API 响应 | risk_score 的圆形仪表盘（0-1） |
| 系统健康面板 | `/health` + `/metrics` | 绿/黄/红状态指示器 |
| Agent 决策日志 | 订单 API 响应 | 所有 Agent 决策的时间线，带时间戳 |

**技术：** Recharts + TanStack Query + Zustand

#### 3.3.6 验收标准

| # | 标准 | 验证方式 |
|---|------|---------|
| 3.1 | WebSocket 在 Agent 决策后 100ms 内推送订单状态更新 | 打开浏览器开发者工具；结账；观察 WebSocket 消息 |
| 3.2 | 结构化日志包含所有 Agent 决策的 JSON 格式 | 结账；检查后端日志；验证 JSON 结构 |
| 3.3 | `/metrics` 端点返回 Prometheus 兼容指标 | `curl /metrics`；验证计数器和仪表盘存在 |
| 3.4 | `/health` 端点检查 DB、Redis 和模型加载状态 | `curl /health`；验证所有检查通过 |
| 3.5 | 前端仪表盘显示 ≥4 个图表（竞价、预测、风险、状态） | 打开前端；验证图表渲染数据 |
| 3.6 | Agent 决策日志在前端可见，带时间戳 | 打开前端；点击订单详情；验证决策时间线 |

---

## 4. 技术架构

### 4.1 系统架构图（升级后）

```
┌─────────────────────────────────────────────────────────────────────┐
│                           React 前端                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ 商品列表  │  │  购物篮  │  │ 订单状态  │  │ 仪表盘 (Recharts)    │  │
│  │          │  │          │  │(WebSocket)│  │  - 竞价图表          │  │
│  │          │  │          │  │          │  │  - 预测趋势线        │  │
│  │          │  │          │  │          │  │  - 风险仪表盘        │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │ HTTP/WebSocket
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI 后端                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ 商品路由  │  │ 订单路由  │  │ Agent路由 │  │ /health /metrics     │  │
│  │          │  │          │  │          │  │ /ws/orders/:id       │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘  │
│       │             │             │                                   │
│       ▼             ▼             ▼                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ 商品服务  │  │ 订单服务  │  │ Agent服务 │  │ WebSocket 管理器     │  │
│  │          │  │          │  │          │  │ (ConnectionManager)  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘  │
│       │             │             │                                   │
│       ▼             ▼             ▼                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ 商品仓储  │  │ 订单仓储  │  │ Redis    │  │ ML 模型              │  │
│  │ (async)  │  │ (async)  │  │ 事件总线  │  │ - MLP 需求预测       │  │
│  └──────────┘  └──────────┘  └──────────┘  │ - XGBoost 欺诈       │  │
│       │             │             │         │ - TF-IDF 分类        │  │
│       ▼             ▼             ▼         └──────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              PostgreSQL 14 + Redis 7                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │ products │  │  orders  │  │order_items│  │warehouse_│    │   │
│  │  │          │  │          │  │           │  │   bids   │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │              agent_decisions                        │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 前端 | React | 18.3 | UI 框架 |
| 前端 | TypeScript | 5.7 | 类型安全 |
| 前端 | Vite | 6.0 | 构建工具 |
| 前端 | Recharts | 2.x | 数据可视化 |
| 前端 | TanStack Query | 5.x | 数据获取 + 缓存 |
| 前端 | Zustand | 4.x | 状态管理 |
| 后端 | Python | 3.12 | 运行时 |
| 后端 | FastAPI | 0.115 | API 框架 |
| 后端 | SQLAlchemy | 2.0 | ORM |
| 后端 | asyncpg | 0.29 | 异步 PostgreSQL 驱动 |
| 后端 | Redis | 7.x | 缓存 + 消息代理 |
| 后端 | redis-py | 5.x | Redis 客户端 |
| 后端 | structlog | 24.x | 结构化日志 |
| 后端 | prometheus-client | 0.21 | 指标 |
| 后端 | PyTorch | 2.3 | MLP 训练 |
| 后端 | XGBoost | 2.0 | 欺诈分类器 |
| 后端 | SHAP | 0.45 | 模型可解释性 |
| 后端 | scikit-learn | 1.4 | TF-IDF + Logistic Regression |
| 后端 | pytest | 8.3 | 测试 |
| 后端 | httpx | 0.28 | HTTP 客户端 (TestClient) |
| 数据库 | PostgreSQL | 14+ | 关系数据存储 |
| 基础设施 | Docker | 24+ | 容器化 |
| 基础设施 | Docker Compose | 2.20+ | 多服务编排 |

### 4.3 环境变量

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/fulfillcrew

# Redis
REDIS_URL=redis://localhost:6379/0

# ML 模型
DEMAND_MODEL_PATH=ml_models/demand_prediction/models/demand_predictor.pt
FRAUD_MODEL_PATH=ml_models/fraud_detection/models/fraud_detector.json
CATEGORY_MODEL_PATH=ml_models/product_category_classifier/models/classifier.pkl

# 后端
BACKEND_PORT=8000
BACKEND_LOG_LEVEL=info
CORS_ORIGINS=http://localhost:5173,http://localhost:8080

# 前端
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_WS_BASE_URL=ws://127.0.0.1:8000
```

---

## 5. 非功能需求

| # | 需求 | 目标 | 理由 |
|---|------|------|------|
| N1 | API 响应时间（p95） | < 200ms | 对演示可接受；真实系统目标 <100ms |
| N2 | WebSocket 延迟 | < 100ms | 前端实时感知 |
| N3 | 数据库查询时间（p95） | < 50ms | 异步查询应快速 |
| N4 | 测试覆盖率 | ≥ 80% | 作品集项目标准 |
| N5 | Docker 构建时间 | < 120s | CI/CD 合理 |
| N6 | Docker 镜像大小 | < 500MB | Python + ML 模型较重；需要多阶段构建 |
| N7 | 前端包大小 | < 500KB | Vite tree-shaking 应保持较小 |
| N8 | 并发 WebSocket 连接 | ≥ 100 | 足够演示和压测 |
| N9 | 模型推理时间 | < 50ms | MLP 和 XGBoost 轻量；CPU 上应快速 |
| N10 | 日志保留 | 30 天 | 足够开发和演示 |

---

## 6. API 规格变更

### 6.1 新增端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| WS | `/ws/orders/{order_id}` | WebSocket 连接，实时订单更新 | 无 |
| GET | `/health` | 综合健康检查（DB、Redis、模型） | 无 |
| GET | `/metrics` | Prometheus 指标端点 | 无 |

### 6.2 修改的端点

**POST /orders**（响应增强）：

```json
{
    "order_id": "uuid",
    "order_status": "created",
    "order_total": 123.45,
    "selected_warehouse": "Warehouse A",
    "risk_score": 0.23,
    "fraud_status": "approved",
    "predicted_demand_next_7_days": 45,
    "restock_recommendation": "no restock needed",
    "bids": [...],
    "decision_log": [
        {
            "agent": "FraudDetectionAgent",
            "message": "Risk score 0.23; status approved.",
            "timestamp": "2026-07-12T14:30:00Z"
        }
    ],
    "course_trace": [...],
    "model_evaluations": [
        {
            "model_name": "Demand Prediction MLP",
            "score": 45,
            "mae": 32.5,
            "shap_explanation": null
        },
        {
            "model_name": "Fraud Detection XGBoost",
            "score": 0.23,
            "roc_auc": 0.94,
            "shap_explanation": {
                "shipping_distance": 0.05,
                "is_new_user": 0.08,
                "order_total": 0.02
            }
        }
    ]
}
```

**GET /agents/model-evaluations**（增强实时指标）：

```json
{
    "models": [
        {
            "model_name": "Demand Prediction MLP",
            "status": "loaded",
            "mae": 32.5,
            "mape": 0.15,
            "r2": 0.82
        },
        {
            "model_name": "Fraud Detection XGBoost",
            "status": "loaded",
            "roc_auc": 0.94,
            "pr_auc": 0.71
        }
    ]
}
```

---

## 7. 风险评估与缓解

| # | 风险 | 可能性 | 影响 | 缓解措施 |
|---|------|--------|------|---------|
| R1 | PostgreSQL 异步驱动复杂度 | 中 | 中 | 使用 SQLAlchemy 2.0 异步模式；保持查询简单 |
| R2 | XGBoost 在小数据集上过拟合 | 中 | 高 | 使用交叉验证；正则化；早停 |
| R3 | SHAP 与 PyTorch 依赖冲突 | 低 | 中 | 训练与推理使用分离的虚拟环境或 Docker 容器 |
| R4 | WebSocket 连接泄漏 | 中 | 中 | 在断开连接时实现 ConnectionManager 清理 |
| R5 | 开发环境 Redis 不可用 | 中 | 低 | 提供本地 Docker Compose（含 Redis）；测试时回退到内存事件总线 |
| R6 | 前端包大小因 Recharts 超标 | 低 | 中 | 使用 tree-shaking；仅导入需要的图表组件 |
| R7 | Docker 构建超过时间限制 | 中 | 低 | 多阶段构建；缓存 pip/npm 层；使用 slim 基础镜像 |
| R8 | 首次训练未达到 MAE/ROC-AUC 目标 | 高 | 中 | 迭代特征工程；尝试替代架构；诚实记录结果 |

---

## 8. 成功标准

升级被视为成功，需满足以下全部条件：

1. **后端启动** 时 PostgreSQL + Redis 就绪，且 `/health` 检查通过
2. **54 个原始测试** 仍然通过（向后兼容）
3. **新测试** 覆盖阶段 1-3，覆盖率 ≥ 80%
4. **ML 模型** 在真实数据上训练完成，评估指标已记录
5. **WebSocket** 实时推送订单状态到前端
6. **前端仪表盘** 至少显示 4 个图表，带实时数据
7. **Docker Compose** 一条命令启动完整栈（前端 + 后端 + PostgreSQL + Redis）
8. **README** 已更新，双语文档涵盖新架构

---

*文档路径：`2.1_代码项目/03_FulfillCrew/docs/PRD_upgrade_v1.md`*
