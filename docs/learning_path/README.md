# FulfillCrew（智仓通）学习路径总览

> **最后更新**：2026-07-13  
> **适用版本**：v2.0  
> **作者**：项目作者 & 软件工程导师

---

## 🎯 项目适合谁？

| 人群 | 适合度 | 说明 |
|------|--------|------|
| **计算机本科生** | ⭐⭐⭐⭐⭐ | 三门课程（COMP315 / COMP310 / ELEC320）的期末项目，从 0 到 1 的完整工程实践 |
| **转码/自学者** | ⭐⭐⭐⭐⭐ | 涵盖前端、后端、AI、DevOps 全栈，是理解现代软件工程的最佳入门项目 |
| **面试准备者** | ⭐⭐⭐⭐⭐ | 33 道高频面试题 + 8 章技术原理深入文档，覆盖实习/初级/中级后端/全栈岗位 |
| **想理解 Multi-Agent 系统的人** | ⭐⭐⭐⭐⭐ | 从 BaseAgent 到 Contract Net Protocol，6 个 Agent 协作的完整实现 |
| **想学习 MLOps 的人** | ⭐⭐⭐⭐ | PyTorch MLP + XGBoost + SHAP + TF-IDF，模型可解释性实践 |

---

## 🗺️ 三条推荐学习路径

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FulfillCrew 学习路径地图                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  路径一：快速上手（30分钟）                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  clone & run │───▶│  checkout    │───▶│  Swagger     │                  │
│  │  Docker      │    │  第一个订单   │    │  Dashboard   │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                                             │
│  路径二：面试突击（3天）                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  elevator    │───▶│  33道Q&A     │───▶│  代码走读    │                  │
│  │  pitch       │    │  速查        │    │  练习        │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                                             │
│  路径三：深度原理（4周 × 5天/周）                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ Week 1   │─▶│ Week 2   │─▶│ Week 3   │─▶│ Week 4   │                    │
│  │ Cloud    │  │ Multi-   │  │ Neural   │  │ Engineer │                    │
│  │ Computing│  │ Agent    │  │ Networks │  │ Upgrade  │                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📚 路径详解

### 路径一：快速上手（30 分钟）

> 📄 文件：`docs/learning_path/00_quickstart.md`

**目标**：从 `git clone` 到看到第一个订单完成，建立对系统的直观认知。

| 步骤 | 内容 | 预计时间 |
|------|------|----------|
| 1 | 克隆项目 → Docker Compose 启动 | 5 分钟 |
| 2 | 打开前端 → 添加商品 → 结账 | 5 分钟 |
| 3 | 观察 WebSocket 实时推送 | 5 分钟 |
| 4 | 浏览 Swagger UI 理解 API | 10 分钟 |
| 5 | 查看 Dashboard 可视化组件 | 5 分钟 |

**前置知识**：已安装 Docker Desktop、了解基本的 HTTP 请求概念。

---

### 路径二：面试突击（3 天）

> 📄 文件：`docs/learning_path/02_interview_prep.md`

**目标**：能够在面试中流畅讲解项目，回答高频技术问题，完成代码走读。

| 天数 | 内容 | 预计时间 |
|------|------|----------|
| Day 1 | 项目 elevator pitch（15 秒版 + 3 分钟版） | 2 小时 |
| Day 2 | 33 道高频问题速查（链接到 interview_qa.md） | 4 小时 |
| Day 3 | 5 段代码走读练习 | 3 小时 |

**前置知识**：已通读 `docs/technical_guide/01_architecture_overview.md`。

---

### 路径三：深度原理（4 周，每周 5 天）

> 📄 文件：`docs/learning_path/01_module_by_module.md`

**目标**：逐模块深入理解代码，能够独立修改、扩展系统。

#### Week 1: Cloud Computing（COMP315）

| 天数 | 主题 | 代码路径 | 预计时间 |
|------|------|----------|----------|
| Day 1 | 数据清洗流水线 | `data_cleaning/` | 1 小时 |
| Day 2 | FastAPI 后端入门 | `backend/main.py`, `backend/api/` | 2 小时 |
| Day 3 | React 前端基础 | `frontend/src/main.tsx` | 2 小时 |
| Day 4 | Docker 部署 | `docker-compose.yml`, `Dockerfile` | 1.5 小时 |
| Day 5 | 整合测试 + 问题排查 | `tests/` | 1.5 小时 |

#### Week 2: Multi-Agent Systems（COMP310）

| 天数 | 主题 | 代码路径 | 预计时间 |
|------|------|----------|----------|
| Day 1 | BaseAgent 设计模式 | `backend/agents/base_agent.py` | 1 小时 |
| Day 2 | Contract Net Protocol | `backend/agents/coordinator_agent.py`, `warehouse_agent.py` | 2 小时 |
| Day 3 | 订单履约流水线 | `backend/services/order_service.py` | 2 小时 |
| Day 4 | Agent 编排与决策日志 | `backend/agents/` 全部 | 1.5 小时 |
| Day 5 | 扩展：添加新 Agent | 自定义实现 | 2 小时 |

#### Week 3: Neural Networks（ELEC320）

| 天数 | 主题 | 代码路径 | 预计时间 |
|------|------|----------|----------|
| Day 1 | MLP 原理 + PyTorch 实现 | `ml_models/demand_prediction/` | 2 小时 |
| Day 2 | XGBoost + SHAP 可解释性 | `ml_models/fraud_detection/` | 2 小时 |
| Day 3 | TF-IDF + LogisticRegression | `ml_models/product_category_classifier/` | 1.5 小时 |
| Day 4 | 模型评估指标 | `backend/services/order_service.py` 中指标收集 | 1.5 小时 |
| Day 5 | 替换自己的模型 | 自定义实现 | 2 小时 |

#### Week 4: Engineering Upgrade（v2.0）

| 天数 | 主题 | 代码路径 | 预计时间 |
|------|------|----------|----------|
| Day 1 | SQLAlchemy 2.0 async + Repository 模式 | `backend/database/`, `backend/repositories/` | 2 小时 |
| Day 2 | Redis 事件总线 + 异步通信 | `backend/infrastructure/event_bus.py` | 1.5 小时 |
| Day 3 | WebSocket 实时推送 | `backend/api/websocket.py`, `frontend/src/hooks/useOrderSocket.ts` | 1.5 小时 |
| Day 4 | 可观测性（structlog + Prometheus） | `backend/infrastructure/logging.py`, `metrics.py` | 1.5 小时 |
| Day 5 | 系统健康检查 + 性能优化 | `backend/api/health.py`, `api/metrics.py` | 1.5 小时 |

---

## 🔬 按需深入（技术原理专题）

> 📄 文件：`docs/learning_path/03_deep_dive.md`

| 你想理解... | 推荐阅读 | 对应代码 |
|-------------|----------|----------|
| FastAPI 异步生命周期 | `technical_guide/03_backend_deep_dive.md` | `backend/main.py` |
| Contract Net Protocol | `technical_guide/04_multi_agent_system.md` | `backend/agents/coordinator_agent.py` |
| MLP 前向传播原理 | `technical_guide/05_ml_models_deep_dive.md` | `ml_models/demand_prediction/` |
| Docker 多阶段构建 | `technical_guide/07_docker_deployment.md` | `Dockerfile` |
| 前端 React 并发特性 | `technical_guide/02_frontend_deep_dive.md` | `frontend/src/main.tsx` |
| 可观测性体系 | `technical_guide/06_infrastructure_observability.md` | `backend/infrastructure/` |

---

## 🛠️ 排错指南

> 📄 文件：`docs/learning_path/04_troubleshooting.md`

覆盖以下常见问题：
- Docker 启动失败
- 数据库连接问题
- 模型加载失败（fallback 机制）
- WebSocket 连接不上
- 前端构建失败

---

## 📁 文档索引

```
docs/
├── learning_path/                    ← 你在这里
│   ├── README.md                     ← 本文件：学习路径总览
│   ├── 00_quickstart.md              ← 30分钟快速上手
│   ├── 01_module_by_module.md        ← 4周逐模块学习
│   ├── 02_interview_prep.md          ← 3天面试突击
│   ├── 03_deep_dive.md               ← 按需深度阅读
│   └── 04_troubleshooting.md         ← 常见问题排查
│
├── adr/                              ← 10篇架构决策记录
│   ├── ADR-001-fastapi-async-backend.md
│   ├── ADR-002-sqlalchemy-postgresql-persistence.md
│   ├── ADR-003-repository-pattern.md
│   ├── ADR-004-redis-inmemory-event-bus.md
│   ├── ADR-005-contract-net-protocol.md
│   ├── ADR-006-react-typescript-vite-frontend.md
│   ├── ADR-007-observability-structlog-prometheus.md
│   ├── ADR-008-websocket-realtime-updates.md
│   ├── ADR-009-docker-compose-deployment.md
│   └── ADR-010-ml-model-selection.md
│
├── interview/
│   └── interview_qa.md               ← 33道高频面试题 + 参考答案
│
├── technical_guide/                  ← 8章技术原理深入文档
│   ├── 01_architecture_overview.md
│   ├── 02_frontend_deep_dive.md
│   ├── 03_backend_deep_dive.md
│   ├── 04_multi_agent_system.md
│   ├── 05_ml_models_deep_dive.md
│   ├── 06_infrastructure_observability.md
│   ├── 07_docker_deployment.md
│   └── 08_interview_qa.md
│
├── system_design.md
├── course_mapping.md
├── deployment.md
└── 中文项目介绍.md
```

---

## ✅ 学习里程碑

| 里程碑 | 检验标准 | 预计时间 |
|--------|----------|----------|
| 🥉 **青铜**：能跑起来 | Docker 启动成功，完成一次 checkout | 30 分钟 |
| 🥈 **白银**：能讲清楚 | 能画出架构图，解释 6 个 Agent 的分工 | 1 周 |
| 🥇 **黄金**：能改代码 | 能独立添加一个 Agent 或替换一个 ML 模型 | 3 周 |
| 💎 **钻石**：能面试 | 能流畅回答 33 道面试题中的任意 20 道 | 4 周 |

---

## 💡 学习建议

1. **先跑起来，再读代码**。不要一上来就逐行读源码，先让系统运行起来，建立直观感受。
2. **带着问题读文档**。例如："WebSocket 是如何把订单状态推给前端的？" → 去读 `backend/api/websocket.py` 和 `frontend/src/hooks/useOrderSocket.ts`。
3. **动手改代码**。把欺诈阈值从 0.65 改成 0.5，观察订单行为变化。把仓库数量从 3 个改成 5 个，看竞价逻辑如何工作。
4. **画架构图**。面试时要求你手绘架构图，提前练习，确保能默写出来。
5. **记录自己的理解**。每学完一个模块，写一段 200 字的总结，用自己的话解释核心概念。

---

> 🚀 **准备好开始了吗？** 先从 [`00_quickstart.md`](./00_quickstart.md) 开始，30 分钟内看到第一个订单！
