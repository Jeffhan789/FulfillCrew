# FulfillCrew 技术原理深入文档 —— 总览

> **目标读者**：正在学习本项目、准备技术面试的开发者。本文档假设你已具备 Python、JavaScript 基础，希望深入理解每个技术选型的"为什么"。

---

## 1. 项目定位：一个"教学级"工程作品集

FulfillCrew（智仓通）不是 toy project，也不是 enterprise SaaS。它刻意设计在**"学生能读懂、面试官能追问"**的甜蜜点上：

- **比 CRUD 有深度**：Multi-Agent 协调、ML 推理、事件总线、WebSocket 实时推送
- **比微服务简单**：单 backend 进程，6 个 Agent 以内聚的 Python class 实现，不引入分布式复杂度
- **三门课程映射清晰**：COMP315（云计算）→ 架构与部署；COMP310（多智能体）→ Agent 协调；ELEC320（神经网络）→ ML 模型

---

## 2. v2.0 架构全景图

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                              Browser (User)                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Nginx (frontend container)                                            │
│  • Serves React SPA static assets (built by Vite)                      │
│  • Proxies /api/* → backend:8000                                       │
│  • Proxies /health, /docs, /openapi.json → backend:8000                │
│  • Proxies /ws/* → backend:8000 (WebSocket upgrade)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    Docker network: fulfillcrew-network
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  FastAPI (backend container) — async Python 3.12                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  API Layer (Routers)                                             │   │
│  │  /products, /orders, /agents, /health, /metrics, /ws/orders      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Service Layer (OrderService)                                    │   │
│  │  Orchestrates 6 agents: Order, Fraud, Inventory, Coordinator,    │   │
│  │  DemandPrediction, Warehouse (x3)                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Repository Layer (SQLAlchemy 2.0 async)                         │   │
│  │  OrderRepository, ProductRepository, AgentDecisionRepository,    │   │
│  │  WarehouseBidRepository                                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Infrastructure Layer                                            │   │
│  │  PostgreSQL (asyncpg), Redis (pub/sub), structlog, Prometheus   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ PostgreSQL  │  │    Redis    │  │  ML Models  │
│  (持久化)    │  │  (事件总线)  │  │  (磁盘加载)  │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## 3. 技术选型决策矩阵

| 决策点 | 选型 | 为什么选它 | 面试中如何表达 |
|--------|------|-----------|-------------|
| 前端框架 | React 18 + TypeScript | 生态最大，TypeScript 提供类型安全，面试中几乎必问 | "React 18 的并发特性（Concurrent Features）让我们在不阻塞 UI 的情况下处理大量订单状态更新" |
| 构建工具 | Vite | 比 Create React App 快 10-100 倍，HMR 即时反馈 | "Vite 使用 esbuild 预构建依赖，开发服务器启动在毫秒级，非常适合快速迭代" |
| 后端框架 | FastAPI | 原生 async/await 支持，自动生成 OpenAPI 文档，Pydantic 类型校验 | "FastAPI 基于 Starlette（ASGI），单个 worker 可以处理数千并发连接，非常适合事件驱动的 Agent 系统" |
| ORM | SQLAlchemy 2.0 async | Python 生态最成熟的 ORM，2.0 版原生支持 asyncpg | "SQLAlchemy 2.0 的 `Mapped` 和 `mapped_column` 语法让类型推断更精确，配合 `async_sessionmaker` 实现全异步数据库操作" |
| 数据库 | PostgreSQL 15 | 支持 JSON、数组、全文搜索，ACID 保证订单一致性 | "PostgreSQL 的 ACID 特性对电商订单至关重要，我们使用 `asyncpg` 驱动实现零阻塞的异步查询" |
| 事件总线 | Redis pub/sub + InMemory fallback | 开发/测试环境无需 Redis 也能运行，降低上手门槛 | "Redis pub/sub 实现服务间解耦，同时提供 InMemoryEventBus 作为 fallback，体现防御性编程" |
| 日志 | structlog | 结构化 JSON 日志，便于后续接入 ELK/Loki | "structlog 的 processor 链将日志统一格式化为 JSON，每个字段可索引，比字符串拼接日志更易查询" |
| 监控 | Prometheus client | 云原生事实标准，可被 Grafana 直接消费 | "我们暴露了 `orders_total`、`order_processing_duration` 等自定义指标，配合 Prometheus 做 SLI 监控" |
| WebSocket | FastAPI 原生 | 无需额外依赖，与 HTTP 路由统一管理 | "FastAPI 的 WebSocket 端点与 HTTP 路由共享同一个 ASGI 应用，通过 ConnectionManager 管理订单级别的连接" |
| ML 框架 | PyTorch + XGBoost + scikit-learn | 分别覆盖神经网络、梯度提升、传统机器学习 | "PyTorch 用于 MLP 需求预测，XGBoost 用于欺诈检测（集成 SHAP 可解释性），sklearn 用于 TF-IDF 文本分类" |
| 部署 | Docker Compose + Nginx | 单机多容器编排，适合教学与演示 | "Docker Compose 声明式编排，配合 Nginx 反向代理实现前后端分离部署，health check 保证服务依赖顺序" |

---

## 4. 核心数据流：从下单到履约

```
用户点击 Checkout
    │
    ▼
POST /orders ──→ OrderService.create_order()
    │
    ├──→ FraudDetectionAgent.score()          [ML 推理]
    │    ├── predict_risk() → risk_score [0,1]
    │    └── threshold 0.65 → approved / review_required
    │
    ├──→ InventoryAgent.check_stock()           [库存检查]
    │    └── 缺货 → 直接返回 rejected_out_of_stock
    │
    ├──→ CoordinatorAgent.request_bids()        [Contract Net Protocol]
    │    ├── Warehouse A, B, C 分别 bid()
    │    └── min(bid) → 选出 winner
    │
    ├──→ DemandPredictionAgent.predict()      [ML 推理]
    │    └── sum(predict_demand(product)) → 7天预测
    │
    ├──→ InventoryAgent.reserve_stock()         [库存预留] (仅 approved)
    │
    └──→ _persist_order()                       [PostgreSQL 持久化]
         ├── OrderRepository.create_order()
         ├── OrderRepository.add_items()
         ├── AgentDecisionRepository.save()
         ├── WarehouseBidRepository.save()
         └── ProductRepository.update_stock()
    │
    └──→ WebSocket 推送 → 前端实时更新
```

**关键设计决策**：
1. **先 fraud 后 inventory**：如果订单明显欺诈，无需检查库存，节省一次查询
2. **先 inventory 后 bidding**：如果缺货，无需触发仓库竞价，减少计算
3. **库存预留放在最后**：只有 fraud_status == approved 时才扣减库存，避免审核中订单占库存
4. **全异步持久化**：`_persist_order` 使用 `async with AsyncSessionLocal()` 在单个事务中提交所有变更

---

## 5. 目录结构映射

```
FulfillCrew/
├── data_cleaning/          # COMP315: Node.js 数据清洗
│   ├── data_processing.js
│   ├── raw_products/
│   └── cleaned_products/
├── frontend/               # COMP315: React 18 + TS + Vite 前端
│   ├── src/main.tsx                 # 主应用组件（SPA）
│   ├── src/components/              # 6 个 Dashboard 组件
│   ├── src/hooks/useOrderSocket.ts  # WebSocket Hook
│   ├── nginx.conf                   # 反向代理配置
│   └── Dockerfile                   # 多阶段构建
├── backend/                # COMP315 + COMP310: FastAPI + Multi-Agent
│   ├── main.py                      # ASGI 入口 + lifespan
│   ├── api/                         # 路由层（products, orders, agents, health, metrics, websocket）
│   ├── agents/                      # 6 个 Agent 实现
│   ├── services/                    # 业务逻辑（OrderService）
│   ├── database/                    # SQLAlchemy 2.0 async 模型 + 引擎
│   ├── repositories/                # Repository 模式封装
│   ├── infrastructure/              # 事件总线、日志、指标、配置
│   └── schemas.py                   # Pydantic 请求/响应模型
├── ml_models/              # ELEC320: 3 个 ML 模块
│   ├── demand_prediction/           # PyTorch MLP
│   ├── fraud_detection/             # XGBoost + SHAP
│   └── product_category_classifier/ # TF-IDF + LogisticRegression
├── tests/                  # pytest + vitest 测试
├── docs/                   # 设计文档
├── docker-compose.yml      # 生产编排（backend + frontend + postgres + redis + nginx）
├── docker-compose.dev.yml  # 开发编排（热重载）
└── Dockerfile              # 后端多阶段构建
```

---

## 6. 继续阅读

| 章节 | 内容 | 对应面试考点 |
|------|------|-------------|
| [02 前端技术深入](02_frontend_deep_dive.md) | React 18 并发、Vite 构建优化、Recharts 数据可视化、WebSocket 实时通信 | 前端性能优化、Hooks 原理、WebSocket 心跳机制 |
| [03 后端技术深入](03_backend_deep_dive.md) | FastAPI async 生命周期、SQLAlchemy 2.0 async、Repository 模式、Pydantic 验证 | Python async/await、ORM 设计模式、数据库事务 |
| [04 多智能体系统](04_multi_agent_system.md) | Contract Net Protocol、Agent 基类设计、竞价策略、决策日志 | 分布式协调、竞价算法、可解释 AI |
| [05 机器学习模型](05_ml_models_deep_dive.md) | PyTorch MLP 架构、XGBoost + SHAP、TF-IDF + LR、特征工程 | 神经网络前向传播、梯度提升原理、模型可解释性 |
| [06 基础设施与可观测性](06_infrastructure_observability.md) | Redis/InMemory 事件总线、structlog 结构化日志、Prometheus 指标、健康检查 | 事件驱动架构、可观测性三大支柱、熔断与降级 |
| [07 Docker 与部署](07_docker_deployment.md) | Docker Compose 服务编排、Nginx 反向代理、多阶段构建、health check 依赖链 | 容器化原理、反向代理、CI/CD 基础 |
| [08 面试问答](08_interview_qa.md) | 高频面试题 + 参考答案 + 追问方向 | 全栈技术面试 |
