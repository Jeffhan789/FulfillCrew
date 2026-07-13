# FulfillCrew 架构演进故事

> 从 v1.0 课程作业到 v2.0 工程化系统的升级历程，每个决策背后的 trade-off 分析。

---

## 目录

1. [v1.0：课程作业的原型](#10-课程作业的原型)
2. [v2.0 升级总览](#20-升级总览)
3. [升级决策详解](#3-升级决策详解)
4. [未来路线图](#4-未来路线图)
5. [如何向评审者讲述演进故事](#5-如何向评审者讲述演进故事)

---

## 1.0：课程作业的原型

### 1.1 原始状态

v1.0 是一个典型的**课程作业级**项目：

```
frontend/
  ├── index.html          # 静态 HTML
  └── app.js              # 原生 JS，无框架

backend/
  ├── main.py             # 单文件 FastAPI，所有逻辑在一起
  └── models.py           # Pydantic 模型 + 内存字典存储

ml_models/
  ├── demand_prediction/
  │   └── predict.py      # 纯启发式函数
  └── fraud_detection/
      └── predict.py      # 纯启发式函数
```

### 1.2 原始技术栈

| 层级 | 技术 |
|------|------|
| 前端 | 原生 HTML + JavaScript（无框架） |
| 后端 | Python 3.11 + FastAPI + Pydantic v1 |
| 存储 | 内存字典（dict[str, Product]） |
| 智能体 | 3 个 Agent（Order, Inventory, Coordinator） |
| ML | 纯启发式函数，无训练接口 |
| 部署 | 手动运行 `uvicorn` |

### 1.3 原始系统的局限

1. **前端**：原生 JS 难以维护，无组件复用，无类型检查
2. **存储**：服务重启数据丢失，无法并发访问，无查询能力
3. **架构**：所有逻辑在 `main.py` 中，单体函数 300+ 行
4. **ML**：只有启发式，无真实模型训练/推理接口
5. **可观测性**：print 调试，无日志、无指标、无健康检查
6. **部署**：需要手动安装依赖，环境不一致

---

## 2.0 升级总览

### 2.1 升级矩阵

| 维度 | v1.0 | v2.0 | 升级理由 |
|------|------|------|----------|
| 前端 | 原生 JS | React 18 + TypeScript + Vite | 组件化、类型安全、工程化 |
| 前端图表 | 无 | Recharts 6 个 Dashboard | 数据可视化、架构复盘展示价值 |
| 实时通信 | 无 | WebSocket | 实时订单状态推送 |
| 后端 ORM | 内存字典 | SQLAlchemy 2.0 async + PostgreSQL | 持久化、ACID、可查询 |
| 数据访问 | 直接操作 dict | Repository 模式 | 抽象、可测试、可替换 |
| 智能体 | 3 个 | 6 个 | 完整课程映射 |
| ML 框架 | 纯启发式 | PyTorch MLP + XGBoost + SHAP | 真实模型接口 + 可解释性 |
| 事件总线 | 无 | Redis / InMemory | 解耦、可扩展 |
| 日志 | print | structlog JSON | 可观测、可聚合 |
| 指标 | 无 | Prometheus | 监控、SLA |
| 健康检查 | 无 | /health 分级检查 | 运维友好 |
| 部署 | 手动 | Docker Compose | 环境一致性、一键启动 |
| 反向代理 | 无 | Nginx | 静态服务、API 代理、SPA 回退 |

### 2.2 架构对比图

**v1.0：**
```
Browser → FastAPI (单文件)
            └── 内存字典
```

**v2.0：**
```
Browser → Nginx
            ├── / → React SPA (静态文件)
            ├── /api/* → FastAPI
            │               ├── PostgreSQL (持久化)
            │               ├── Redis (缓存/消息)
            │               ├── 6 Agents (协调)
            │               ├── ML Models (推理)
            │               └── WebSocket (实时)
            ├── /health → FastAPI
            └── /docs → FastAPI Swagger
```

---

## 3. 升级决策详解

### 3.1 前端：原生 JS → React 18 + TypeScript

**决策过程：**

> "v1.0 的前端是原生 JavaScript，大约 200 行代码实现商品列表和购物篮。随着功能增加（搜索、排序、过滤、Dashboard 图表），代码变得难以维护。"

**考虑的选项：**

| 方案 | 优势 | 劣势 | 选择 |
|------|------|------|------|
| 保持原生 JS | 无构建步骤、简单 | 难以维护、无组件复用 | ❌ |
| Vue 3 | 学习曲线平缓、中文文档好 | 当前可视化与组件选型已围绕 React 验证 | ❌ |
| React 18 + JS | 生态成熟 | 无类型安全 | ❌ |
| **React 18 + TS** | 类型安全、组件化、架构复盘通用 | 需要构建步骤 | ✅ |

**关键设计决策：**
- **Vite 而不是 CRA**：CRA 已官方弃用，Vite 构建速度快 10 倍以上
- **无状态管理库**：`useState` + `useMemo` 足够，避免过度工程
- **Recharts 而不是 D3**：声明式 API 更适合 React，学习成本低

**架构复盘讲述要点：**
> "v1.0 的前端是原生 JS，维护困难。升级到 React + TypeScript 后，类型系统让接口契约清晰（`OrderResponse`、`WarehouseBid`），6 个 Dashboard 组件可以独立开发和测试。"

---

### 3.2 存储：内存字典 → PostgreSQL + SQLAlchemy 2.0

**决策过程：**

> "v1.0 用 Python 字典存储数据，重启后所有数据消失。课程作业可以接受，但架构复盘项目中需要展示持久化能力。"

**考虑的选项：**

| 方案 | 优势 | 劣势 | 选择 |
|------|------|------|------|
| 保持内存 | 简单、快 | 数据丢失、无法并发 | ❌ |
| SQLite | 零配置、单文件 | 并发写入弱、无网络访问 | ❌ |
| **PostgreSQL** | ACID、JSON 支持、并发好 | 需要 Docker 运行 | ✅ |
| MongoDB | 灵活 schema | 事务支持弱、不符合课程映射 | ❌ |

**SQLAlchemy 2.0 的选型理由：**
- 异步原生支持（`AsyncSession`、`selectinload`）
- `Mapped[T]` 类型注解——IDE 友好、可静态检查
- 与 FastAPI 生态深度集成

**Repository 模式的引入：**

v1.0 中数据访问直接在 Service 中写：
```python
# v1.0 — 反模式
products[product_id].quantity -= item.quantity
```

v2.0 中抽象为 Repository：
```python
# v2.0 — Repository 模式
await product_repo.update_stock(product_id, -item.quantity)
```

**架构复盘讲述要点：**
> "v1.0 用内存字典，适合演示但不适合工程。升级到 PostgreSQL + SQLAlchemy 2.0 async 后，数据有了 ACID 保证。Repository 模式抽象了数据访问层，未来如果要换数据库（如 MongoDB），只需替换 Repository 实现。"

---

### 3.3 智能体：3 个 → 6 个 + Contract Net Protocol

**决策过程：**

> "v1.0 只有 Order、Inventory、Coordinator 三个 Agent，无法完整映射 COMP310 Multi-Agent Systems 的课程内容。"

**新增的 Agent：**

| Agent | 课程映射 | 职责 |
|-------|----------|------|
| Fraud Detection Agent | ELEC320 二分类 | 订单风险评估 |
| Demand Prediction Agent | ELEC320 MLP 回归 | 未来需求预测 |
| Warehouse Agent × 3 | COMP310 协商 | 仓库竞价（Contract Net） |

**Contract Net Protocol 的引入：**

v1.0 中仓库选择是硬编码的：
```python
# v1.0
selected_warehouse = "Warehouse A"  # 硬编码
```

v2.0 中引入竞价机制：
```python
# v2.0
bids, winner = self.coordinator_agent.request_bids(item_count)
# 每个 Warehouse Agent 独立计算 bid
```

**架构复盘讲述要点：**
> "v1.0 的仓库选择是硬编码的，v2.0 引入了简化版 Contract Net Protocol。3 个 Warehouse Agent 基于 workload、stock、distance、speed 计算可解释竞价，Coordinator 选择最低 bid。这让代码直接映射到 COMP310 的课程内容，同时也展示了**可解释 AI** 的实践。"

---

### 3.4 ML：纯启发式 → PyTorch + XGBoost + SHAP

**决策过程：**

> "v1.0 的 ML 模块是纯启发式函数，虽然可运行，但架构复盘中难以展示对神经网络和机器学习的理解。"

**需求预测的演进：**

```python
# v1.0 — 纯启发式
def predict_demand(features):
    return features["quantity"] * 0.7  # 简单粗暴

# v2.0 — PyTorch MLP + fallback
class DemandMLP(nn.Module):
    def __init__(self, input_dim=9):
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
        )

def predict_demand(features):
    if model_exists:
        return pytorch_inference(features)
    else:
        return heuristic_fallback(features)  # 优雅降级
```

**欺诈检测的演进：**

```python
# v1.0 — 纯启发式
def predict_risk(features):
    return 0.3 if features["is_new_user"] else 0.1

# v2.0 — XGBoost + SHAP
class FraudDetector:
    def __init__(self):
        if model_file_exists:
            self.model = xgb.XGBClassifier()
            self.model.load_model("fraud_xgb.json")
            self.explainer = shap.TreeExplainer(self.model)
        else:
            self.model = LightweightFraudClassifier()  # fallback
```

**SHAP 的引入理由：**
- 不仅是"这个订单有风险"，还要解释"为什么"
- TreeExplainer 对 XGBoost 的 SHAP 计算是精确的（不是近似）
- 架构复盘中可以展示对**模型可解释性（XAI）**的理解

**架构复盘讲述要点：**
> "v1.0 的 ML 是启发式函数，v2.0 设计了**稳定的推理接口**。Demand Prediction 使用 PyTorch MLP（2 隐藏层 + Dropout），输入 9 维特征。Fraud Detection 使用 XGBoost + SHAP，SHAP 提供基于博弈论的特征贡献解释。每个模型都有 fallback 机制——没有训练数据时系统仍可运行。"

---

### 3.5 可观测性：print → structlog + Prometheus

**决策过程：**

> "v1.0 用 print 调试，上线后无法排查问题。需要引入结构化日志和指标。"

**日志系统的演进：**

```python
# v1.0
print(f"Order created: {order_id}")

# v2.0
logger.info(
    "order.created",
    order_id=order_id,
    user_id=request.user_id,
    event="order.created",
)
# 输出: {"event": "order.created", "order_id": "...", "user_id": "...", "level": "info", "timestamp": "..."}
```

**为什么 JSON 日志？**
- 可直接被 ELK/Loki 消费
- 支持按字段搜索和聚合
- Fallback 机制：structlog 不可用时自动回退到纯文本

**指标系统的引入：**

```python
orders_total = Counter("fulfillcrew_orders_total", "Total orders processed", ["status"])
order_processing_duration = Histogram("fulfillcrew_order_processing_seconds", ...)
```

- Counter：追踪订单状态分布（created / review_required / rejected）
- Histogram：追踪处理延迟，自动计算 P50/P95/P99
- Gauge：追踪最新风险评分

**架构复盘讲述要点：**
> "v1.0 用 print 调试，无法在生产环境使用。v2.0 引入 structlog 输出 JSON 结构化日志，每个事件包含 order_id 等上下文，便于分布式追踪。同时引入 Prometheus 指标——Counter 追踪订单量、Histogram 追踪处理延迟、Gauge 追踪风险评分。"

---

### 3.6 部署：手动运行 → Docker Compose

**决策过程：**

> "v1.0 需要手动安装 Python 依赖、Node 依赖，然后分别启动前后端。评审者不可能花 10 分钟看你配环境。"

**Docker 多阶段构建的价值：**

```dockerfile
# 前端 Dockerfile
FROM node:20-alpine AS builder   # 构建阶段：需要 Node
RUN npm ci && npm run build

FROM nginx:alpine                # 运行阶段：只需要 Nginx
COPY --from=builder /app/dist /usr/share/nginx/html
# 最终镜像：~20MB，无 Node、无 npm
```

**docker-compose.yml 的服务编排：**

```yaml
services:
  postgres: ...    # 先启动
  redis: ...       # 先启动
  backend:         # 等 pg + redis healthy 后启动
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
  frontend:        # 等 backend healthy 后启动
    depends_on:
      backend: { condition: service_healthy }
```

**架构复盘讲述要点：**
> "v1.0 需要手动配环境，v2.0 用 Docker Compose 实现**一键启动**。前端用多阶段构建，最终镜像只有 20MB。服务启动有依赖链：postgres → redis → backend → frontend，每个服务只在前置依赖 healthy 后才启动。"

---

### 3.7 配置管理：硬编码 → 环境变量

**v1.0 的问题：**
```python
# v1.0 — 硬编码
DATABASE_URL = "postgresql://user:pass@localhost/db"
```

**v2.0 的解决方案：**
```python
# v2.0 — 环境变量 + 默认值
@dataclass(frozen=True)
class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fulfillcrew"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

- `frozen=True`：配置不可变，防止运行时修改
- 环境变量 + 默认值：开发环境无需配置，生产环境通过 `.env` 注入

---

## 4. 未来路线图

### 4.1 短期（1-2 个月）

| 特性 | 技术方案 | 价值 |
|------|----------|------|
| 端到端测试 | Playwright | 验证完整用户流程 |
| 性能测试 | Locust | 发现并发瓶颈 |
| CI/CD | GitHub Actions | 自动化测试和部署 |
| 订单历史页面 | React Router | 展示更多前端能力 |

### 4.2 中期（3-6 个月）

| 特性 | 技术方案 | 价值 |
|------|----------|------|
| 用户认证 | JWT + OAuth2 | 真实用户系统 |
| 消息队列 | Kafka / RabbitMQ | 异步订单处理 |
| 缓存层 | Redis Cache | 减少数据库查询 |
| 模型服务化 | TorchServe / Triton | 独立 ML 推理服务 |

### 4.3 长期（6-12 个月）

| 特性 | 技术方案 | 价值 |
|------|----------|------|
| Kubernetes 部署 | Helm Charts | 云原生弹性伸缩 |
| 微服务拆分 | gRPC / REST | 独立部署 Agent |
| 实时分析 | Flink / Spark Streaming | 实时欺诈检测 |
| A/B 测试框架 | Split / LaunchDarkly | 模型效果评估 |

---

## 5. 如何向评审者讲述演进故事

### 5.1 2 分钟版本

> "这个项目经历了两个版本。v1.0 是课程作业级的原型——原生 JS 前端、内存存储、纯启发式 ML。v2.0 做了系统性工程化升级：React + TypeScript 前端，PostgreSQL + SQLAlchemy 2.0 async 持久化，6 个 Agent 的 Contract Net Protocol 协调，PyTorch MLP + XGBoost + SHAP 的 ML 层，structlog + Prometheus 的可观测性，Docker Compose 的一键部署。
>
> 每个升级都有明确的 trade-off：前端选 React 而不是 Vue 因为架构复盘通用性；数据库选 PostgreSQL 而不是 SQLite 因为要展示 ACID 和并发；ML 模型设计 fallback 机制确保 MVP 可运行。
>
> 下一步计划：引入消息队列做异步处理，模型服务化，部署到 Kubernetes。"

### 5.2 回答"为什么升级"的标准框架

**STAR 法则：**
- **S**ituation：v1.0 的状态和局限
- **T**ask：需要解决的具体问题
- **A**ction：选择的方案和 trade-off
- **R**esult：升级后的效果和数据

**示例："为什么引入 Repository 模式？"**

> **S**：v1.0 中数据访问直接在 Service 里操作字典，业务逻辑和数据访问混在一起。
> **T**：我需要让数据访问可测试、可替换。
> **A**：引入 Repository 模式，每个表一个 Repository，Service 通过 Repository 接口访问数据。Trade-off 是增加了文件数量，但获得了抽象和可测试性。
> **R**：现在可以 mock Repository 做单元测试，不需要启动真实数据库。如果未来换数据库，只需替换 Repository 实现。

### 5.3 避免的坑

❌ **不要说"因为老师要求"**——要转化为"因为课程知识需要工程化落地"

❌ **不要说"因为 React 更流行"**——要说"因为类型安全和组件化适合这个项目的复杂度"

❌ **不要只讲做了什么**——要讲"为什么这样做，考虑过什么替代方案"

✅ **要展示工程判断力**——"我在 X 和 Y 之间选择了 X，因为..."

✅ **要承认不足**——"v2.0 还没有消息队列，如果订单量增大，我会引入 Kafka"

✅ **要有下一步计划**——"下一步我计划..."

---

> 架构演进故事是架构复盘中最有力的叙事。它展示了你不只是"做了一个项目"，而是**持续思考、迭代优化**的工程师。🚀
